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

    def get_url(self):
        if not self.org_file_id:
            return ''

        if self.org_file_id.startswith('cloud'):
            arr = self.org_file_id.split('/')
            arr[0] = 'https:'
            arr[2] = arr[2].split('.')[1] + '.tcb.qcloud.la'
            return '/'.join(arr)
        else:
            return self.org_file_id

    def to_json(self):
        return {
            "id": self.id,
            "userOpenId": self.user_openId,
            "healthyStar": self.healthy_star,
            "deliciousStar": self.delicious_star,
            "location": self.location,
            "picUrl": self.get_url(),
            "fileId": self.file_id,
            "type": self.type,
            "date": self.date.strftime("%Y-%m-%d"),
            "createAt": self.createdAt.strftime("%Y-%m-%d %H:%M"),
            "updateAt": self.updatedAt.strftime("%Y-%m-%d %H:%M"),
        }
