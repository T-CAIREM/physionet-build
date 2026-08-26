from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional

from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from events.models import Event, EventDataset
from project.authorization.events import has_access_to_event_dataset
from project.models import AccessPolicy, DUASignature, DataAccessRequest, PublishedProject
from user.enums import RequiredField
from user.models import Training, TrainingType
from physionet.utility import get_country_code, get_client_ip


def get_public_projects_query():
    """Returns query filter for public published projects"""
    return Q(access_policy=AccessPolicy.OPEN)


def get_restricted_projects_query(user):
    """Returns query filter for restricted published projects accessible by a specified user"""
    dua_signatures = DUASignature.objects.filter(user=user)
    query = Q(access_policy=AccessPolicy.RESTRICTED) & Q(duasignature__in=dua_signatures)
    return query


def get_credentialed_projects_query(user):
    """Returns query filter for credentialed published projects accessible by a specified user"""

    dua_signatures = DUASignature.objects.filter(user=user)

    completed_training = (
        Training.objects.get_valid()
        .filter(user=user)
        .values_list("training_type")
    )
    not_completed_training = TrainingType.objects.exclude(pk__in=completed_training)
    required_training_complete = ~Q(required_trainings__in=not_completed_training)

    accepted_data_access_requests = DataAccessRequest.objects.filter(
        requester=user, status=DataAccessRequest.ACCEPT_REQUEST_VALUE
    )

    contributor_review_with_access = Q(
        access_policy=AccessPolicy.CONTRIBUTOR_REVIEW
    ) & Q(data_access_requests__in=accepted_data_access_requests)

    credentialed_with_dua_signed = Q(
        access_policy=AccessPolicy.CREDENTIALED
    ) & Q(duasignature__in=dua_signatures)

    query = required_training_complete & (
        contributor_review_with_access | credentialed_with_dua_signed
    )
    return query


def get_projects_accessible_through_events(user):
    """Returns query filter for published projects accessible by a specified user through events"""
    events_all = Event.objects.filter(Q(host=user) | Q(participants__user=user))

    active_events = set(events_all.filter(end_date__gte=datetime.now()))

    accessible_datasets = EventDataset.objects.filter(event__in=active_events, is_active=True)

    accessible_projects_ids = []
    for event_dataset in accessible_datasets:
        if has_access_to_event_dataset(user, event_dataset):
            accessible_projects_ids.append(event_dataset.dataset.id)

    query = Q(id__in=accessible_projects_ids)
    return query


def get_accessible_projects(user):
    """
    Returns all published projects accessible by a specified user
    """
    query = Q(deprecated_files=False)

    query &= get_public_projects_query()

    if user.is_authenticated:
        query |= get_restricted_projects_query(user)

    if user.is_credentialed:
        query |= get_credentialed_projects_query(user)

    query |= get_projects_accessible_through_events(user)

    return PublishedProject.objects.filter(query).distinct()


def can_access_project(project, user, request=None):
    """
    Checks if the project is accessible by the user
    Users may access a project through different ways, for example, thorough direct download on the physionet website,
    or through s3 bucket links, or gcs storage.
    This function only checks access to the project in general, users might still not be able to access the files
    even if they can access the project.

    Args:
        project: The project instance
        user: The user requesting access
        request: The HTTP request object (optional, needed for country-based restrictions)
    """
    if project.deprecated_files:
        return False

    # Check country-based restrictions if project is georestricted and request is provided
    if project.georestricted and request:
        ip = get_client_ip(request)
        country_code = get_country_code(ip)
        if country_code in settings.BLOCKED_REGIONS:
            return False

    if project.access_policy == AccessPolicy.OPEN:
        return True
    elif project.access_policy == AccessPolicy.RESTRICTED:
        return user.is_authenticated and DUASignature.objects.filter(project=project, user=user).exists()
    elif project.access_policy == AccessPolicy.CREDENTIALED:
        return (
            user.is_authenticated
            and user.is_credentialed
            and DUASignature.objects.filter(project=project, user=user).exists()
            and Training.objects.get_valid()
            .filter(training_type__in=project.required_trainings.all(), user=user)
            .count()
            == project.required_trainings.count()
        )
    elif project.access_policy == AccessPolicy.CONTRIBUTOR_REVIEW:
        return (
            user.is_authenticated
            and user.is_credentialed
            and DataAccessRequest.objects.get_active(
                project=project,
                requester=user,
                status=DataAccessRequest.ACCEPT_REQUEST_VALUE
            ).exists()
            and Training.objects.get_valid()
            .filter(training_type__in=project.required_trainings.all(), user=user)
            .count()
            == project.required_trainings.count()
        )
    return False


def can_view_project_files(project, user, request=None):
    """
    Checks if the project files are  directly accessible by the user
    Currently used to allow direct file downloads and to show project files on the platform
    """
    return can_access_project(project, user, request) and project.allow_file_downloads


class DatasetAccessReason:
    """
    Closed enumeration of the reasons `evaluate_dataset_access` can return.

    The values are part of the API consumed by out-of-tree callers (the dataset
    applications package), so they are stable strings, not integers.
    """

    OK = 'ok'
    NOT_AUTHENTICATED = 'not_authenticated'
    NOT_CREDENTIALED = 'not_credentialed'
    DUA_UNSIGNED = 'dua_unsigned'
    TRAINING_MISSING = 'training_missing'
    TRAINING_EXPIRED = 'training_expired'
    REQUEST_NOT_APPROVED = 'request_not_approved'
    REQUEST_EXPIRED = 'request_expired'
    DOWNLOADS_DISABLED = 'downloads_disabled'
    EMBARGOED = 'embargoed'
    DEPRECATED = 'deprecated'
    GEORESTRICTED = 'georestricted'
    EVENT_ENDED = 'event_ended'


@dataclass(frozen=True)
class DatasetAccessDecision:
    """
    The structured result of evaluating access to a published project.

    `allowed` is the value of the shared predicate:

        allowed  <=>  ( can_view_project_files(project, user, request)
                        or has_active_event_access(project, user) )
                      and not project.embargo_active()
                      and not project.deprecated_files

    It deliberately carries no application-level terms (app status, bindings,
    path availability); callers add those themselves.

    `reason` is a member of `DatasetAccessReason` naming the first gate that
    failed, or `ok` when `allowed` is True.
    """

    allowed: bool
    reason: str
    can_access: bool
    can_view_files: bool
    allow_file_downloads: bool
    event_access: bool
    event_access_types: List[str]
    embargo_until: Optional[datetime]
    deprecated: bool
    georestricted: bool
    access_policy: str
    valid_until: Optional[datetime]


def _event_datasets_granting_access(project, user):
    """
    Returns the EventDataset objects of `project` that currently grant `user` access.

    Delegates to `has_access_to_event_dataset`, the platform's shared helper, so
    that this stays consistent with the website rather than restating its rules.
    """
    if not user.is_authenticated:
        return []

    # TODO(P12): `has_access_to_event_dataset` checks only `event.end_date`, while
    # `EventDataset.is_accessible()` (events/models.py) also rejects an event that has
    # not started yet. The two callers therefore disagree about a not-yet-started
    # event. Do not add a start_date check here in isolation: align the two helpers.
    return [
        event_dataset
        for event_dataset in EventDataset.objects.filter(dataset=project, is_active=True).select_related('event')
        if has_access_to_event_dataset(user, event_dataset)
    ]


def has_active_event_access(project, user):
    """
    Checks if the user has access to any of the project's datasets through an event.

    Thin project-level wrapper over `has_access_to_event_dataset`; it adds no rules
    of its own.
    """
    return bool(_event_datasets_granting_access(project, user))


def _has_lapsed_event_grant(project, user):
    """
    Checks if the user belongs to an event that has (or had) this project as a dataset,
    but that no longer grants access. Used only to name a denial reason.
    """
    if not user.is_authenticated:
        return False

    return (
        EventDataset.objects.filter(dataset=project)
        .filter(Q(event__host=user) | Q(event__participants__user=user))
        .exists()
    )


def _geo_blocked(project, request=None, client_ip=None):
    """
    Evaluates the georestriction of a project against an attested client IP if one was
    supplied, and otherwise against the request's own IP. Returns False when the project
    is not georestricted or when no IP is available to evaluate.
    """
    if not project.georestricted:
        return False

    ip = client_ip if client_ip else (get_client_ip(request) if request is not None else None)
    if not ip:
        return False

    return get_country_code(ip) in settings.BLOCKED_REGIONS


def _training_expiry(project, user):
    """
    Returns the earliest expiry among the user's valid trainings for the project's
    required training types, or None when nothing expires (or nothing is required).
    """
    required_training_ids = list(project.required_trainings.values_list('id', flat=True))
    if not required_training_ids or not user.is_authenticated:
        return None

    expiry_by_type = {}
    unbounded_types = set()
    for training in Training.objects.get_valid().filter(user=user, training_type_id__in=required_training_ids):
        if training.valid_datetime is None:
            unbounded_types.add(training.training_type_id)
        else:
            previous = expiry_by_type.get(training.training_type_id)
            if previous is None or training.valid_datetime > previous:
                expiry_by_type[training.training_type_id] = training.valid_datetime

    expiries = [expiry for type_id, expiry in expiry_by_type.items() if type_id not in unbounded_types]
    return min(expiries) if expiries else None


def _training_denial_reason(project, user):
    """
    Returns `training_expired` / `training_missing` when the project's required trainings
    are not satisfied, and None when they are.
    """
    required_trainings = project.required_trainings.all()
    required_count = required_trainings.count()
    if not required_count:
        return None

    valid_training_types = set(
        Training.objects.get_valid()
        .filter(user=user, training_type__in=required_trainings)
        .values_list('training_type_id', flat=True)
    )
    missing_type_ids = set(required_trainings.values_list('id', flat=True)) - valid_training_types
    if not missing_type_ids:
        return None

    # `Training.is_expired()` is used rather than `TrainingQuerySet.get_expired()`, which
    # inner-joins the course table and therefore never returns a document- or URL-based
    # training (those have no course). Filed separately; not worked around anywhere else.
    for training in Training.objects.filter(user=user, training_type_id__in=missing_type_ids).select_related(
        'training_type', 'course'
    ):
        if training.training_type.required_field == RequiredField.PLATFORM and training.course is None:
            continue
        if training.is_expired():
            return DatasetAccessReason.TRAINING_EXPIRED

    return DatasetAccessReason.TRAINING_MISSING


def _data_access_request_valid_until(project, user):
    """
    Returns the latest expiry among the user's active data access requests for the
    project, or None when one of them never expires.
    """
    valid_until_values = list(
        DataAccessRequest.objects.get_active(
            project=project, requester=user, status=DataAccessRequest.ACCEPT_REQUEST_VALUE
        ).values_list('valid_until', flat=True)
    )
    if not valid_until_values or any(value is None for value in valid_until_values):
        return None

    return max(valid_until_values)


def _event_valid_until(event_datasets):
    """
    Returns the end of the last day of the latest event granting access, since event
    access is evaluated against `event.end_date` as a date.
    """
    end_dates = [event_dataset.event.end_date for event_dataset in event_datasets if event_dataset.event.end_date]
    if not end_dates:
        return None

    end_of_last_day = datetime.combine(max(end_dates), time.max)
    if settings.USE_TZ:
        return timezone.make_aware(end_of_last_day)

    return end_of_last_day


def _policy_denial_reason(project, user):
    """
    Returns the reason the project's access policy denies this user. Only called when
    the policy gates were not satisfied, so it always names a gate.
    """
    # The branches below walk the same gates as `can_access_project`, in the same order,
    # and each `return` at the end of a branch is defensive: it is only reachable if that
    # function grows a gate that this one does not know about.
    if project.access_policy == AccessPolicy.RESTRICTED:
        return DatasetAccessReason.DUA_UNSIGNED

    if project.access_policy == AccessPolicy.CREDENTIALED:
        if not user.is_credentialed:
            return DatasetAccessReason.NOT_CREDENTIALED
        if not DUASignature.objects.filter(project=project, user=user).exists():
            return DatasetAccessReason.DUA_UNSIGNED
        return _training_denial_reason(project, user) or DatasetAccessReason.NOT_CREDENTIALED

    if project.access_policy == AccessPolicy.CONTRIBUTOR_REVIEW:
        if not user.is_credentialed:
            return DatasetAccessReason.NOT_CREDENTIALED
        if not DataAccessRequest.objects.get_active(
            project=project, requester=user, status=DataAccessRequest.ACCEPT_REQUEST_VALUE
        ).exists():
            if DataAccessRequest.objects.filter(
                project=project, requester=user, status=DataAccessRequest.ACCEPT_REQUEST_VALUE
            ).exists():
                return DatasetAccessReason.REQUEST_EXPIRED
            return DatasetAccessReason.REQUEST_NOT_APPROVED
        return _training_denial_reason(project, user) or DatasetAccessReason.REQUEST_NOT_APPROVED

    # An OPEN project that is not accessible was denied by a gate evaluated before this
    # function was reached.
    return DatasetAccessReason.NOT_AUTHENTICATED


def evaluate_dataset_access(project, user, request=None, *, client_ip=None):
    """
    Evaluates the shared dataset access predicate and returns a DatasetAccessDecision.

    This is the single implementation of the predicate. The website, the dataset
    applications package and any other consumer call it rather than restating the
    rules, so that all of them agree.

    Args:
        project: The PublishedProject instance
        user: The user requesting access (may be anonymous)
        request: The HTTP request object (optional, used for country-based restrictions)
        client_ip: An attested end-user IP address (optional). When given, the
            georestriction is evaluated against it instead of the request's own IP,
            which is what makes the decision meaningful for a server-to-server caller
            acting on behalf of an end user.

    The returned `valid_until` is when the access lapses: the latest expiry across the
    routes that currently grant it (the access policy, and an event grant), each route
    expiring with the earliest of its own terms. It is None when nothing grants access,
    and when a granting route never expires.
    """
    deprecated = bool(project.deprecated_files)
    embargo_active = bool(project.embargo_active())
    geo_blocked = _geo_blocked(project, request=request, client_ip=client_ip)

    # `can_access_project` is called without the request so that the georestriction is
    # evaluated exactly once, above, against the attested IP when there is one.
    can_access = can_access_project(project, user, None) and not geo_blocked
    can_view_files = can_access and project.allow_file_downloads

    event_datasets = _event_datasets_granting_access(project, user)
    event_access = bool(event_datasets)

    allowed = (can_view_files or event_access) and not embargo_active and not deprecated

    if allowed:
        reason = DatasetAccessReason.OK
    elif not user.is_authenticated and project.access_policy != AccessPolicy.OPEN:
        reason = DatasetAccessReason.NOT_AUTHENTICATED
    elif deprecated:
        reason = DatasetAccessReason.DEPRECATED
    elif embargo_active:
        reason = DatasetAccessReason.EMBARGOED
    elif geo_blocked:
        reason = DatasetAccessReason.GEORESTRICTED
    elif not can_access:
        # An event grant that has lapsed is named specifically: it is the thing that
        # changed for this user, and it is more actionable than the policy gate.
        if _has_lapsed_event_grant(project, user):
            reason = DatasetAccessReason.EVENT_ENDED
        else:
            reason = _policy_denial_reason(project, user)
    else:
        reason = DatasetAccessReason.DOWNLOADS_DISABLED

    # `valid_until` is when the access itself lapses: the latest expiry across the routes
    # that currently grant it, because access survives while any one route holds. Within a
    # route it is the earliest of that route's own terms, because the route lapses with the
    # first of them. A granting route that never expires leaves the access unbounded.
    route_expiries = []
    if can_view_files:
        policy_terms = []
        if project.access_policy == AccessPolicy.CONTRIBUTOR_REVIEW:
            policy_terms.append(_data_access_request_valid_until(project, user))
        if project.access_policy in (AccessPolicy.CREDENTIALED, AccessPolicy.CONTRIBUTOR_REVIEW):
            policy_terms.append(_training_expiry(project, user))
        policy_terms = [term for term in policy_terms if term is not None]
        route_expiries.append(min(policy_terms) if policy_terms else None)
    if event_access:
        route_expiries.append(_event_valid_until(event_datasets))

    if route_expiries and all(expiry is not None for expiry in route_expiries):
        valid_until = max(route_expiries)
    else:
        valid_until = None

    return DatasetAccessDecision(
        allowed=allowed,
        reason=reason,
        can_access=can_access,
        can_view_files=can_view_files,
        allow_file_downloads=bool(project.allow_file_downloads),
        event_access=event_access,
        event_access_types=sorted({event_dataset.access_type for event_dataset in event_datasets}),
        embargo_until=project.embargo_end_date(),
        deprecated=deprecated,
        georestricted=bool(project.georestricted),
        access_policy=AccessPolicy(project.access_policy).name,
        valid_until=valid_until,
    )
