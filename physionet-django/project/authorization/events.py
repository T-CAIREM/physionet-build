from django.utils import timezone


def has_event_access(user, event):
    """
    Checks if the user has access to the event
    """
    return event.host == user or event.participants.filter(user=user).exists()


def has_access_to_event_dataset(user, event_dataset):
    """
    Checks if the user has access to the event dataset
    """
    # TODO: this helper checks only `event.end_date`, while `EventDataset.is_accessible()`
    # (events/models.py) also rejects an event that has not started yet. The two therefore
    # disagree about a not-yet-started event. Behaviour is deliberately left unchanged here;
    # the two should be aligned together, in one change, once the intended rule is decided.
    if not has_event_access(user, event_dataset.event):
        return False

    if not event_dataset.is_active:
        return False

    if timezone.now().date() > event_dataset.event.end_date:
        return False

    return True
