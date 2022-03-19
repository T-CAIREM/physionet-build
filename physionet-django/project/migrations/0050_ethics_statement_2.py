# Generated by Django 2.2.25 on 2022-01-20 15:34

from django.db import migrations, models
import django.db.models.deletion
import project.modelcomponents.fields
import project.modelcomponents.metadata


def migrate_forward(apps, schema_editor):
    ActiveProject = apps.get_model("project", "ActiveProject")
    ArchivedProject = apps.get_model("project", "ArchivedProject")
    PublishedProject = apps.get_model("project", "PublishedProject")

    ActiveProject.objects.update(ethics_statement="The authors declare no ethics concerns.")
    ArchivedProject.objects.update(ethics_statement="The authors declare no ethics concerns.")
    PublishedProject.objects.update(ethics_statement="")


def migrate_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    MIGRATE_AFTER_INSTALL = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('project', '0049_ethics_statement_1'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
        migrations.AlterField(
            model_name='activeproject',
            name='ethics_statement',
            field=project.modelcomponents.fields.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='ethics_statement',
            field=project.modelcomponents.fields.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='ethics_statement',
            field=project.modelcomponents.fields.SafeHTMLField(blank=True),
        ),
    ]