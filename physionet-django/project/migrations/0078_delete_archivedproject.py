# Generated by Django 4.1.13 on 2024-09-25 04:41

from django.db import migrations


class Migration(migrations.Migration):
    MIGRATE_AFTER_INSTALL = True

    dependencies = [
        ("project", "0077_fix_some_references"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ArchivedProject",
        ),
    ]
