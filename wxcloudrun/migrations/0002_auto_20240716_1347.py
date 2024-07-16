# Generated by Django 3.2.8 on 2024-07-16 13:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dinners',
            name='beauty_star',
            field=models.SmallIntegerField(default=0, max_length=2),
        ),
        migrations.AlterField(
            model_name='counters',
            name='createdAt',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 16, 13, 47, 14, 786127)),
        ),
        migrations.AlterField(
            model_name='counters',
            name='updatedAt',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 16, 13, 47, 14, 786153)),
        ),
        migrations.AlterField(
            model_name='dinners',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='dinners',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='dinners',
            name='updatedAt',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='users',
            name='createdAt',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 16, 13, 47, 14, 786891)),
        ),
        migrations.AlterField(
            model_name='users',
            name='updatedAt',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 16, 13, 47, 14, 786913)),
        ),
    ]