# Generated by Django 2.2.27 on 2022-02-23 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0063_auto_20220528_2248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataaccess',
            name='platform',
            field=models.PositiveSmallIntegerField(choices=[(0, 'local'), (1, 'aws-open-data'), (2, 'aws-s3'), (3, 'gcp-bucket'), (4, 'gcp-bigquery'), (5, 'gcp-research-environment')]),
        ),
    ]
