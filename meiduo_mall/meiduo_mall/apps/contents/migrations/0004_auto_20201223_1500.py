# Generated by Django 2.2.5 on 2020-12-23 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contents', '0003_auto_20201223_1227'),
    ]

    operations = [
        migrations.RenameField(
            model_name='content',
            old_name='creat_time',
            new_name='create_time',
        ),
        migrations.RenameField(
            model_name='contentcategory',
            old_name='creat_time',
            new_name='create_time',
        ),
    ]
