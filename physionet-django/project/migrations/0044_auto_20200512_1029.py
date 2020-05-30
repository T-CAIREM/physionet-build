# Generated by Django 2.2.9 on 2020-05-12 14:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0043_incremental_storage_size_2'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataAccessRequestReviewer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('is_revoked', models.BooleanField(default=False)),
                ('revocation_date', models.DateTimeField(null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_access_request_reviewers', to='project.PublishedProject')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_access_request_reviewers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='dataaccessrequestreviewer',
            constraint=models.UniqueConstraint(fields=('project', 'reviewer'), name='unique project reviewer'),
        ),
    ]
