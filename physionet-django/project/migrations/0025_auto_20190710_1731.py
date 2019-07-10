# Generated by Django 2.1.7 on 2019-07-10 21:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0024_auto_20190708_1810'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectType',
            fields=[
                ('id', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20)),
                ('description', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='activeproject',
            name='resource_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activeprojects', to='project.ProjectType'),
        ),
        migrations.AlterField(
            model_name='archivedproject',
            name='resource_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archivedprojects', to='project.ProjectType'),
        ),
        migrations.AlterField(
            model_name='publishedproject',
            name='resource_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publishedprojects', to='project.ProjectType'),
        ),
    ]
