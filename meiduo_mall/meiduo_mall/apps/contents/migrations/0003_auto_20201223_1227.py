# Generated by Django 2.2.5 on 2020-12-23 04:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contents', '0002_auto_20201223_1223'),
    ]

    operations = [
        migrations.RenameField(
            model_name='content',
            old_name='create_time',
            new_name='creat_time',
        ),
        migrations.RenameField(
            model_name='contentcategory',
            old_name='create_time',
            new_name='creat_time',
        ),
    ]
