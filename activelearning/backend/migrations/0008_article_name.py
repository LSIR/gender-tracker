# Generated by Django 2.2.5 on 2019-12-04 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_auto_20191202_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='name',
            field=models.CharField(default='No article title', max_length=200),
            preserve_default=False,
        ),
    ]
