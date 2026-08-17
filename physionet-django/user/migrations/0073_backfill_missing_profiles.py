from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    """
    Create a blank Profile for every user that has none.

    Users created outside RegistrationForm, or by a create_user call that
    failed part way through, can be left without a Profile. Every
    `user.profile` access then raises RelatedObjectDoesNotExist. A blank
    profile is already a supported state, since create_user defaults the
    name fields to empty strings.
    """
    User = apps.get_model('user', 'User')
    Profile = apps.get_model('user', 'Profile')

    missing = User.objects.filter(profile__isnull=True)
    Profile.objects.bulk_create(
        [Profile(user=user, first_names='', last_name='') for user in missing])


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0072_primary_email_integrity'),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles,
                             migrations.RunPython.noop),
    ]
