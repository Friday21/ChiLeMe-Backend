from datetime import datetime

from django.db import models


# Create your models here.
class Users(models.Model):
    id = models.AutoField
    alias = models.CharField(max_length=256, default="")
    open_id = models.CharField(max_length=256, default="")
    avatar_url = models.CharField(max_length=256, default="")
    phone = models.CharField(max_length=32, default="")
    friends = models.TextField(default="[]")

    createdAt = models.DateTimeField(default=datetime.now(), )
    updatedAt = models.DateTimeField(default=datetime.now(),)

    def __str__(self):
        return "user {}".format(self.alias)

    class Meta:
        db_table = 'Users'  # 数据库表名
