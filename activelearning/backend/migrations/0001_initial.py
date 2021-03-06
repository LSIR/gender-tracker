# Generated by Django 2.2.5 on 2019-10-31 12:31

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Articles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('authors', django.contrib.postgres.fields.jsonb.JSONField()),
                ('tokens', django.contrib.postgres.fields.jsonb.JSONField()),
                ('paragraphs', django.contrib.postgres.fields.jsonb.JSONField()),
                ('sentences', django.contrib.postgres.fields.jsonb.JSONField()),
                ('label_counts', django.contrib.postgres.fields.jsonb.JSONField()),
                ('in_quotes', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='UserLabels',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('labels', django.contrib.postgres.fields.jsonb.JSONField()),
                ('sentence_index', models.IntegerField()),
                ('author_index', django.contrib.postgres.fields.jsonb.JSONField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Articles')),
            ],
        ),
    ]
