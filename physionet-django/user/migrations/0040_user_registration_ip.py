# Generated by Django 2.2.27 on 2022-03-30 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0039_codeofconduct_codeofconductsignature'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='registration_ip',
            field=models.CharField(blank=True, db_index=True, max_length=40, null=True),
        ),
    ]
