# Generated by Django 3.2.13 on 2024-09-03 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moxutils', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='CustomerGroup',
            new_name='group',
        ),
    ]
