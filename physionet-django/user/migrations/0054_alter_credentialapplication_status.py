# Generated by Django 3.2.16 on 2023-03-03 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0053_credentialapplication_reference_verification_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credentialapplication',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Pending'), (1, 'Rejected'), (2, 'Accepted'),
                                                            (3, 'Withdrawn'), (4, 'Revoked')], default=0),
        ),
    ]
