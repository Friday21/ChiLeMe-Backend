import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0003_auto_20250301_0505'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernotes',
            name='comment',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='counters',
            name='createdAt',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 6, 6, 12, 38, 550441)),
        ),
        migrations.AlterField(
            model_name='counters',
            name='updatedAt',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 6, 6, 12, 38, 550459)),
        ),
        migrations.AlterField(
            model_name='users',
            name='createdAt',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 6, 6, 12, 38, 550957)),
        ),
        migrations.AlterField(
            model_name='users',
            name='updatedAt',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 6, 6, 12, 38, 550974)),
        ),
    ]