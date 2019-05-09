# Generated by Django 2.1.7 on 2019-04-05 21:44

from django.db import migrations
import project.models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0011_auto_20190402_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activeproject',
            name='abstract',
            field=project.models.SafeHTMLField(blank=True, max_length=10000),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='acknowledgements',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='background',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='conflicts_of_interest',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='content_description',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='installation',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='methods',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='release_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='usage_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='abstract',
            field=project.models.SafeHTMLField(blank=True, max_length=10000),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='acknowledgements',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='background',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='conflicts_of_interest',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='content_description',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='installation',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='methods',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='release_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='usage_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='legacyproject',
            name='abstract',
            field=project.models.SafeHTMLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='legacyproject',
            name='full_description',
            field=project.models.SafeHTMLField(),
        ),
        migrations.AlterField(
            model_name='license',
            name='dua_html_content',
            field=project.models.SafeHTMLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='license',
            name='html_content',
            field=project.models.SafeHTMLField(default=''),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='abstract',
            field=project.models.SafeHTMLField(blank=True, max_length=10000),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='acknowledgements',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='background',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='conflicts_of_interest',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='content_description',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='full_description',
            field=project.models.SafeHTMLField(default=''),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='installation',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='methods',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='release_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='usage_notes',
            field=project.models.SafeHTMLField(blank=True),
        ),
    ]