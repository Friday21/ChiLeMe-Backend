"""
Migration: add title and source fields to TimeItem
  - title:  页面标题（原 JSON 中的 title 字段）
  - source: 来源，如 browser / app
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0011_time_tracker'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeitem',
            name='title',
            field=models.CharField(max_length=512, default=''),
        ),
        migrations.AddField(
            model_name='timeitem',
            name='source',
            field=models.CharField(max_length=64, default='browser'),
        ),
    ]
