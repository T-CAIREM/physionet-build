# Generated by Django 2.2.27 on 2022-02-21 08:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0061_auto_20220324_0542'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='affiliation',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='anonymousaccess',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='author',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='authorinvitation',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='contact',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='copyeditlog',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='coreproject',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='dataaccess',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='dataaccessrequest',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='dataaccessrequestreviewer',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='documenttype',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='duasignature',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='editlog',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='gcp',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='legacyproject',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='programminglanguage',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='projecttype',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publication',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publishedaffiliation',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publishedauthor',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publishedproject',
            options={
                'default_permissions': ('change',),
                'permissions': [
                    ('can_edit_featured_content', 'Can edit featured content'),
                    ('can_view_access_logs', 'Can view access logs'),
                    ('can_view_project_guidelines', 'Can view project guidelines'),
                    ('can_view_stats', 'Can view stats')
                ]
            },
        ),
        migrations.AlterModelOptions(
            name='publishedpublication',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publishedreference',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='publishedtopic',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='reference',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='storagerequest',
            options={'default_permissions': ('change',)},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='uploadeddocument',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='accesslog',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='dua',
            options={'default_permissions': ('add',)},
        ),
        migrations.AlterModelOptions(
            name='gcplog',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='license',
            options={'default_permissions': ('add',)},
        ),
        migrations.AlterModelOptions(
            name='log',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='activeproject',
            options={'default_permissions': ('change',)},
        ),
        migrations.AlterModelOptions(
            name='archivedproject',
            options={
                'default_permissions': ('change',),
                'permissions': [
                    ('can_assign_editor', 'Can assign editor')
                ]
            },
        ),
    ]
