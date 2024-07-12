from datetime import datetime

from django.db import models


class DinnerType:
    Breakfast = "早餐"
    Dinner = "午餐"
    Lunch = "晚餐"
    Night = "宵夜"


# Create your models here.
class Dinners(models.Model):
    id = models.AutoField
    user_openId = models.CharField(max_length=256, default="")
    healthy_star = models.SmallIntegerField(max_length=2, default=0)
    delicious_star = models.SmallIntegerField(max_length=2, default=0)
    friends_stars = models.TextField(default="[]")
    location = models.CharField(max_length=256, default="")
    pic_url = models.CharField(max_length=256, default="")
    file_id = models.CharField(max_length=256, default="")
    org_file_id = models.CharField(max_length=256, default="")
    type = models.CharField(max_length=32, default="")

    date = models.DateField(default=datetime.now().date())
    createdAt = models.DateTimeField(default=datetime.now(), )
    updatedAt = models.DateTimeField(default=datetime.now(),)

    def __str__(self):
        return "dinner {}".format(self.user_openId)

    class Meta:
        db_table = 'Dinners'  # 数据库表名

    def to_json(self):
        return {
            "id": self.id,
            "user_openId": self.user_openId,
            "healthy_star": self.healthy_star,
            "delicious_star": self.delicious_star,
            "location": self.location,
            "pic_url": self.pic_url,
            "type": self.type,
            "date": self.date.strftime("%Y-%m-%d"),
            "create_at": self.createdA.strftime("%Y-%m-%d %H:%M")
        }
