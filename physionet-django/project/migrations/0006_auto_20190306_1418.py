# Generated by Django 2.1.7 on 2019-03-06 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_auto_20190220_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activeproject',
            name='project_home_page',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='version',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='project_home_page',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='version',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='project_home_page',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='version',
            field=models.CharField(default='', max_length=15),
        ),
    ]