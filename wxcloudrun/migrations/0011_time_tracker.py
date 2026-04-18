"""
Migration: add time tracking models
  - TimeItem    (原始浏览记录，每条含开始时间/耗时/分类/detail/title/source)
  - TimeInsight (每天的 AI 洞察文字，可选)
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0009_auto_20251228_0521'),
    ]

    operations = [
        # ── TimeItem ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='TimeItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('user_open_id', models.CharField(max_length=256, db_index=True)),
                ('record_date',  models.DateField(db_index=True)),
                ('start_time',   models.DateTimeField()),
                ('duration',     models.IntegerField(default=0)),
                ('category',     models.CharField(max_length=64, default='其他')),
                ('title',        models.CharField(max_length=512, default='')),
                ('detail',       models.CharField(max_length=2048)),
                ('domain',       models.CharField(max_length=256, db_index=True)),
                ('source',       models.CharField(max_length=64, default='browser')),
                ('createdAt',    models.DateTimeField(auto_now_add=True)),
                ('updatedAt',    models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'TimeItem',
                'ordering': ['start_time'],
            },
        ),
        migrations.AddConstraint(
            model_name='timeitem',
            constraint=models.UniqueConstraint(
                fields=['user_open_id', 'start_time', 'detail'],
                name='unique_timeitem',
            ),
        ),

        # ── TimeInsight ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='TimeInsight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('user_open_id', models.CharField(max_length=256, db_index=True)),
                ('record_date',  models.DateField()),
                ('insight',      models.TextField(default='')),
                ('createdAt',    models.DateTimeField(auto_now_add=True)),
                ('updatedAt',    models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'TimeInsight',
            },
        ),
        migrations.AddConstraint(
            model_name='timeinsight',
            constraint=models.UniqueConstraint(
                fields=['user_open_id', 'record_date'],
                name='unique_timeinsight_per_day',
            ),
        ),
    ]
