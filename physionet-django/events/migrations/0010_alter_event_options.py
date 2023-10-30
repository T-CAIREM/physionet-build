# Generated by Django 4.2.11 on 2024-05-29 16:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0009_cohostinvitation"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={
                "permissions": [
                    ("view_all_events", "Can view all events in the console"),
                    ("view_event_menu", "Can view event menu in the navbar"),
                    ("add_event_dataset", "Can add a dataset to an event"),
                ]
            },
        ),
    ]