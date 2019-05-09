# Generated by Django 2.1.5 on 2019-02-08 17:10

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_auto_20181231_1623'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegacyProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.CharField(max_length=100)),
                ('abstract', ckeditor.fields.RichTextField(blank=True, default='')),
                ('full_description', ckeditor.fields.RichTextField()),
                ('doi', models.CharField(blank=True, default='', max_length=100)),
                ('version', models.CharField(default='1.0.0', max_length=20)),
                ('resource_type', models.PositiveSmallIntegerField(default=0)),
                ('publish_date', models.DateField()),
                ('citation', models.CharField(blank=True, default='', max_length=1000)),
                ('citation_url', models.URLField(blank=True, default='')),
                ('contact_name', models.CharField(default='PhysioNet Support', max_length=120)),
                ('contact_affiliations', models.CharField(default='MIT', max_length=150)),
                ('contact_email', models.EmailField(default='webmaster@physionet.org', max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='publishedproject',
            name='full_description',
            field=ckeditor.fields.RichTextField(default=''),
        ),
        migrations.AddField(
            model_name='publishedproject',
            name='is_legacy',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='license',
            name='dua_html_content',
            field=ckeditor.fields.RichTextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='license',
            name='dua_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='publication',
            name='citation',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='publishedpublication',
            name='citation',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='publishedreference',
            name='description',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='reference',
            name='description',
            field=models.CharField(max_length=1000),
        ),
    ]