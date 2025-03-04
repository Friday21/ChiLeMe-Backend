import logging
from datetime import datetime

from django.db import models

logger = logging.getLogger('log')


class DinnerType:
    Breakfast = "早餐"
    Dinner = "午餐"
    Lunch = "晚餐"
    Night = "宵夜"


# Create your models here.
class UserNotes(models.Model):
    id = models.AutoField
    user_openId = models.CharField(max_length=256, default="")
    text = models.CharField(max_length=1024, default="")
    category = models.CharField(max_length=256, default="")  # "体育;职场"
    positive = models.IntegerField(default=3)

    date = models.DateField()
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "user notes {}".format(self.user_openId)

    class Meta:
        db_table = 'UserNotes'  # 数据库表名

    def to_json(self):
        return {
            "id": self.id,
            "userOpenId": self.user_openId,
            "text": self.text,
            "category": self.category.split(";"),
            "positive": self.positive,
            "date": self.date.strftime("%Y-%m-%d"),
            "createAt": self.createdAt.strftime("%Y-%m-%d %H:%M"),
            "updateAt": self.updatedAt.strftime("%Y-%m-%d %H:%M"),
        }

    @classmethod
    def to_fake_json(cls):
        return {
            "id": -1,
            "userOpenId": "fake",
            "text": "未识别语音",
            "category": "",
            "positive": 3,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "createAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "updateAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
