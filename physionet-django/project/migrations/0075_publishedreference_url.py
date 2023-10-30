# Generated by Django 4.2.11 on 2024-05-13 20:18

import re

from django.db import migrations, models


def migrate_forward(apps, schema_editor):
    pattern = re.compile(r'\bhttps?://[^\s<>"\']+', re.IGNORECASE)

    PublishedReference = apps.get_model('project', 'PublishedReference')
    for reference in PublishedReference.objects.all():
        m = pattern.search(reference.description)
        if m:
            reference.url = m.group()
            reference.save(update_fields=['url'])


def migrate_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0074_migrate_archived_to_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedreference",
            name="url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_forward, migrate_backward),
    ]