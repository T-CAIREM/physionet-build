# Generated by Django 3.1.14 on 2023-01-10 21:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0048_auto_20221129_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='old_events', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='eventparticipant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='old_event_participants', to=settings.AUTH_USER_MODEL),
        ),
    ]
