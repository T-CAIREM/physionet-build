from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from events.models import Event, EventDataset, EventParticipant
from project.authorization.access import (
    DatasetAccessReason,
    evaluate_dataset_access,
    has_active_event_access,
)
from project.models import (
    AccessPolicy,
    DataAccessRequest,
    DUASignature,
    PublishedProject,
)
from user.enums import TrainingStatus
from user.models import Profile, Training, User


class DatasetAccessTestCase(TestCase):
    """
    Tests for the shared dataset access predicate.

    The demo projects supply the access policies: demopsn is OPEN, demoeicu is
    CREDENTIALED and demoselfmanaged is CONTRIBUTOR_REVIEW. Everything else the tests
    need (users, signatures, trainings, requests, events) is created here, and rolled
    back with the test transaction.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.open_project = PublishedProject.objects.get(slug='demopsn', version='1.0')
        self.credentialed_project = PublishedProject.objects.get(slug='demoeicu', version='2.0.0')
        self.review_project = PublishedProject.objects.get(slug='demoselfmanaged', version='1.0.0')

        self.assertEqual(self.open_project.access_policy, AccessPolicy.OPEN)
        self.assertEqual(self.credentialed_project.access_policy, AccessPolicy.CREDENTIALED)
        self.assertEqual(self.review_project.access_policy, AccessPolicy.CONTRIBUTOR_REVIEW)

        self.user_counter = 0
        self.user = self.create_user()
        self.credentialed_user = self.create_user(is_credentialed=True)

    def create_user(self, is_credentialed=False):
        """Create a user who satisfies none of the projects' requirements."""
        self.user_counter += 1
        suffix = self.user_counter
        user = User.objects.create(
            username=f'accesstest{suffix}',
            email=f'accesstest{suffix}@example.org',
            is_active=True,
            is_credentialed=is_credentialed,
            credential_datetime=timezone.now() if is_credentialed else None,
        )
        Profile.objects.create(user=user, first_names=f'Access{suffix}', last_name='Test')
        return user

    def complete_trainings(self, project, user, process_datetime=None):
        """Give the user an accepted training of each type the project requires."""
        for index, training_type in enumerate(project.required_trainings.all()):
            Training.objects.create(
                user=user,
                slug=f'accesstest{user.id}tr{index}',
                training_type=training_type,
                status=TrainingStatus.ACCEPTED,
                process_datetime=process_datetime or timezone.now(),
            )

    def entitle(self, project, user):
        """Give the user everything the project's access policy requires."""
        DUASignature.objects.create(project=project, user=user)
        self.complete_trainings(project, user)

    def create_event_dataset(self, project, user, end_date=None, is_active=True, access_type=None):
        """Make the user a participant of an event that grants access to the project."""
        self.user_counter += 1
        event = Event.objects.create(
            title=f'Access test event {self.user_counter}',
            category='Datathon',
            host=self.create_user(),
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=end_date or (timezone.now().date() + timedelta(days=7)),
        )
        EventParticipant.objects.create(user=user, event=event)
        event_dataset = EventDataset(event=event, dataset=project, is_active=is_active)
        if access_type is not None:
            event_dataset.access_type = access_type
        event_dataset.save()
        return event_dataset

    # Allowed

    def test_open_project_is_allowed_for_anonymous_user(self):
        decision = evaluate_dataset_access(self.open_project, AnonymousUser())

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.OK)
        self.assertTrue(decision.can_access)
        self.assertTrue(decision.can_view_files)
        self.assertFalse(decision.event_access)
        self.assertEqual(decision.access_policy, 'OPEN')
        self.assertIsNone(decision.valid_until)

    def test_entitled_user_is_allowed_for_credentialed_project(self):
        self.entitle(self.credentialed_project, self.credentialed_user)

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.OK)
        self.assertEqual(decision.access_policy, 'CREDENTIALED')
        self.assertIsNotNone(decision.valid_until)

    # Denials, one per reason

    def test_anonymous_user_is_not_authenticated(self):
        decision = evaluate_dataset_access(self.credentialed_project, AnonymousUser())

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.NOT_AUTHENTICATED)
        self.assertFalse(decision.can_access)

    def test_user_without_credentialing_is_not_credentialed(self):
        decision = evaluate_dataset_access(self.credentialed_project, self.user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.NOT_CREDENTIALED)

    def test_user_without_signature_is_dua_unsigned(self):
        self.complete_trainings(self.credentialed_project, self.credentialed_user)

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertEqual(decision.reason, DatasetAccessReason.DUA_UNSIGNED)

    def test_restricted_project_without_signature_is_dua_unsigned(self):
        self.open_project.access_policy = AccessPolicy.RESTRICTED
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertEqual(decision.reason, DatasetAccessReason.DUA_UNSIGNED)
        self.assertEqual(decision.access_policy, 'RESTRICTED')

    def test_user_without_training_is_training_missing(self):
        DUASignature.objects.create(project=self.credentialed_project, user=self.credentialed_user)

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertEqual(decision.reason, DatasetAccessReason.TRAINING_MISSING)

    def test_user_with_expired_training_is_training_expired(self):
        DUASignature.objects.create(project=self.credentialed_project, user=self.credentialed_user)
        self.complete_trainings(
            self.credentialed_project,
            self.credentialed_user,
            process_datetime=timezone.now() - timedelta(days=100 * 365),
        )

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertEqual(decision.reason, DatasetAccessReason.TRAINING_EXPIRED)

    def test_user_without_request_is_request_not_approved(self):
        self.complete_trainings(self.review_project, self.credentialed_user)

        decision = evaluate_dataset_access(self.review_project, self.credentialed_user)

        self.assertEqual(decision.reason, DatasetAccessReason.REQUEST_NOT_APPROVED)
        self.assertEqual(decision.access_policy, 'CONTRIBUTOR_REVIEW')

    def test_user_with_lapsed_request_is_request_expired(self):
        self.complete_trainings(self.review_project, self.credentialed_user)
        DataAccessRequest.objects.create(
            project=self.review_project,
            requester=self.credentialed_user,
            status=DataAccessRequest.ACCEPT_REQUEST_VALUE,
            decision_datetime=timezone.now() - timedelta(days=400),
            duration=timedelta(days=30),
        )

        decision = evaluate_dataset_access(self.review_project, self.credentialed_user)

        self.assertEqual(decision.reason, DatasetAccessReason.REQUEST_EXPIRED)

    def test_project_with_downloads_disabled_is_downloads_disabled(self):
        self.open_project.allow_file_downloads = False
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.DOWNLOADS_DISABLED)
        self.assertTrue(decision.can_access)
        self.assertFalse(decision.can_view_files)
        self.assertFalse(decision.allow_file_downloads)

    def test_project_under_embargo_is_embargoed(self):
        self.open_project.embargo_files_days = 100 * 365
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.EMBARGOED)
        self.assertIsNotNone(decision.embargo_until)

    def test_project_with_deprecated_files_is_deprecated(self):
        self.open_project.deprecated_files = True
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.DEPRECATED)
        self.assertTrue(decision.deprecated)

    @override_settings(BLOCKED_REGIONS={'localhost'})
    def test_blocked_region_is_georestricted(self):
        self.open_project.georestricted = True
        self.open_project.save()
        request = self.factory.get('/', REMOTE_ADDR='127.0.0.1')

        decision = evaluate_dataset_access(self.open_project, self.user, request)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.GEORESTRICTED)
        self.assertTrue(decision.georestricted)

    def test_ended_event_is_event_ended(self):
        self.create_event_dataset(
            self.credentialed_project,
            self.credentialed_user,
            end_date=timezone.now().date() - timedelta(days=1),
        )

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.EVENT_ENDED)

    # Event access

    def test_event_participant_is_allowed_without_policy_access(self):
        end_date = timezone.now().date() + timedelta(days=7)
        self.create_event_dataset(self.credentialed_project, self.user, end_date=end_date)

        decision = evaluate_dataset_access(self.credentialed_project, self.user)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.OK)
        self.assertFalse(decision.can_access)
        self.assertTrue(decision.event_access)
        self.assertEqual(decision.event_access_types, ['GBQ'])
        self.assertEqual(decision.valid_until.date(), end_date)

    def test_inactive_event_dataset_does_not_grant_access(self):
        self.create_event_dataset(self.credentialed_project, self.user, is_active=False)

        self.assertFalse(has_active_event_access(self.credentialed_project, self.user))
        self.assertFalse(evaluate_dataset_access(self.credentialed_project, self.user).allowed)

    def test_has_active_event_access_matches_the_decision(self):
        self.assertFalse(has_active_event_access(self.credentialed_project, self.user))
        self.assertFalse(has_active_event_access(self.credentialed_project, AnonymousUser()))

        self.create_event_dataset(self.credentialed_project, self.user)

        self.assertTrue(has_active_event_access(self.credentialed_project, self.user))
        self.assertTrue(evaluate_dataset_access(self.credentialed_project, self.user).event_access)

    def test_embargo_denies_an_event_participant(self):
        self.create_event_dataset(self.open_project, self.user)
        self.open_project.embargo_files_days = 100 * 365
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.EMBARGOED)
        self.assertTrue(decision.event_access)

    # valid_until

    def test_valid_until_is_clamped_to_the_data_access_request(self):
        self.complete_trainings(self.review_project, self.credentialed_user)
        DataAccessRequest.objects.create(
            project=self.review_project,
            requester=self.credentialed_user,
            status=DataAccessRequest.ACCEPT_REQUEST_VALUE,
            decision_datetime=timezone.now(),
            duration=timedelta(days=30),
        )

        decision = evaluate_dataset_access(self.review_project, self.credentialed_user)

        self.assertTrue(decision.allowed)
        # The request expires long before the three-year training does.
        self.assertLess(decision.valid_until, timezone.now() + timedelta(days=31))

    def test_valid_until_is_clamped_to_the_training_expiry(self):
        self.entitle(self.credentialed_project, self.credentialed_user)

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        training_type = self.credentialed_project.required_trainings.first()
        self.assertIsNotNone(training_type.valid_duration)
        self.assertLess(decision.valid_until, timezone.now() + training_type.valid_duration + timedelta(days=1))

    def test_valid_until_is_none_when_a_granting_route_never_expires(self):
        # The open policy grants indefinitely, so a shorter event grant must not shorten it.
        self.create_event_dataset(self.open_project, self.user, end_date=timezone.now().date() + timedelta(days=7))

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.can_view_files)
        self.assertTrue(decision.event_access)
        self.assertIsNone(decision.valid_until)

    def test_valid_until_takes_the_later_of_two_granting_routes(self):
        # The event outlasts the training the credentialed policy depends on.
        self.entitle(self.credentialed_project, self.credentialed_user)
        end_date = timezone.now().date() + timedelta(days=2000)
        self.create_event_dataset(self.credentialed_project, self.credentialed_user, end_date=end_date)

        decision = evaluate_dataset_access(self.credentialed_project, self.credentialed_user)

        self.assertTrue(decision.can_view_files)
        self.assertTrue(decision.event_access)
        self.assertEqual(decision.valid_until.date(), end_date)

    # Attested client IP

    @override_settings(BLOCKED_REGIONS={'localhost'})
    def test_attested_client_ip_is_evaluated_instead_of_the_request_ip(self):
        self.open_project.georestricted = True
        self.open_project.save()
        # The request comes from a blocked address, but the end user it acts for does not.
        request = self.factory.get('/', REMOTE_ADDR='127.0.0.1')

        decision = evaluate_dataset_access(self.open_project, self.user, request, client_ip='198.51.100.10')

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.OK)
        self.assertTrue(decision.georestricted)

    @override_settings(BLOCKED_REGIONS={'localhost'})
    def test_attested_client_ip_denies_a_blocked_end_user(self):
        self.open_project.georestricted = True
        self.open_project.save()
        request = self.factory.get('/', REMOTE_ADDR='198.51.100.10')

        decision = evaluate_dataset_access(self.open_project, self.user, request, client_ip='127.0.0.1')

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, DatasetAccessReason.GEORESTRICTED)

    @override_settings(BLOCKED_REGIONS={'localhost'})
    def test_georestriction_is_not_evaluated_without_an_address(self):
        self.open_project.georestricted = True
        self.open_project.save()

        decision = evaluate_dataset_access(self.open_project, self.user)

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.georestricted)
