# Generated by Django 2.2.5 on 2019-11-02 17:26

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_auto_20191031_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='confidence',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None),
            preserve_default=False,
        ),
    ]
