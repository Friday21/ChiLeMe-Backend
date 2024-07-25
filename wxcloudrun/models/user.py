import json
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

    def to_simple_json(self):
        return {
            "alias": self.alias,
            "open_id": self.open_id,
            "avatar_url": self.avatar_url,
        }

    def to_json(self):
        return {
            "alias": self.alias,
            "open_id": self.open_id,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "friends": json.loads(self.friends),
            "createAt": self.createdAt.strftime("%Y-%m-%d %H:%M"),
            "updateAt": self.updatedAt.strftime("%Y-%m-%d %H:%M"),
        }

    def add_friend(self, user):
        friends = json.loads(self.friends)
        for friend in friends:
            if friend['open_id'] == user.open_id:
                friend['alias'] = user.alias
                friend['avatar_url'] = user.avatar_url
                break
        else:
            friends.append(user.to_simple_json())
        self.friends = json.dumps(friends)
        self.save()

    def remove_friend(self, user):
        friends = json.loads(self.friends)
        new_friends = [friend for friend in friends if friend['open_id'] != user.open_id]
        self.friends = json.dumps(new_friends)
        self.save()

    def update_friend_info(self):
        friends = json.loads(self.friends)
        friend_open_ids = [friend['open_id'] for friend in friends]
        users = Users.objects.filter(open_id__in=friend_open_ids).all()
        for user in users:
            user.add_friend(self)