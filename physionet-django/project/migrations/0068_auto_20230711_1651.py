# Generated by Django 3.1.14 on 2023-07-11 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0067_alter_activeproject_core_project_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='affiliations',
            field=models.CharField(max_length=612),
        ),
    ]