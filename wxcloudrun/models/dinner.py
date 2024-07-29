import json
import logging

from django.db import models
from .user import Users

logger = logging.getLogger('log')


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
    beauty_star = models.SmallIntegerField(max_length=2, default=0)
    friends_stars = models.TextField(default="[]")
    location = models.CharField(max_length=256, default="")
    pic_url = models.CharField(max_length=256, default="")
    file_id = models.CharField(max_length=256, default="")
    org_file_id = models.CharField(max_length=256, default="")
    type = models.CharField(max_length=32, default="")

    date = models.DateField()
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

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

    def to_friend_json(self, open_id):
        friends_stars = json.loads(self.friends_stars)
        stars = {
            'healthy_star': 0,
            'delicious_star': 0,
            'beauty_star': 0
        }
        for item in friends_stars:
            if item['from_openId'] == open_id:
                stars['healthy_star'] = item['healthy_star'] * 10
                stars['delicious_star'] = item['delicious_star'] * 10
                stars['beauty_star'] = item['beauty_star'] * 10
                break

        return {
            "id": self.id,
            "userOpenId": self.user_openId,
            "healthyStar": stars['healthy_star'],
            "deliciousStar": stars['delicious_star'],
            "beautyStar": stars['beauty_star'],
            "location": self.location,
            "picUrl": self.get_url(),
            "fileId": self.file_id,
            "type": self.type,
            "date": self.date.strftime("%Y-%m-%d"),
            "createAt": self.createdAt.strftime("%Y-%m-%d %H:%M"),
            "updateAt": self.updatedAt.strftime("%Y-%m-%d %H:%M"),
        }

    def to_json(self):
        return {
            "id": self.id,
            "userOpenId": self.user_openId,
            "healthyStar": self.healthy_star,
            "deliciousStar": self.delicious_star,
            "beautyStar": self.beauty_star,
            "location": self.location,
            "picUrl": self.get_url(),
            "fileId": self.file_id,
            "type": self.type,
            "friends_stars": json.loads(self.friends_stars),
            "date": self.date.strftime("%Y-%m-%d"),
            "createAt": self.createdAt.strftime("%Y-%m-%d %H:%M"),
            "updateAt": self.updatedAt.strftime("%Y-%m-%d %H:%M"),
        }

    def to_self_json(self):
        info = self.to_json()
        open_ids = []
        for friend_star in info['friends_stars']:
            open_ids.append(friend_star['from_openId'])
        open_ids = list(set(open_ids))
        users = Users.objects.filter(open_id__in=open_ids).all()
        open_id_avatar_map = dict()
        for user in users:
            open_id_avatar_map[user.open_id] = user.avatar_url

        friends_avatars = []
        for friend_star in info['friends_stars']:
            friends_avatars.append(open_id_avatar_map.get(friend_star['from_openId'], ''))
        info['friends_avatars'] = list(set(friends_avatars))[:3]
        return info

    def update_start(self, from_openId, healthy_star, delicious_star, beauty_star):
        friends_stars = json.loads(self.friends_stars)
        for item in friends_stars:
            if item['from_openId'] == from_openId:
                item['healthy_star'] = healthy_star if healthy_star != 0 else item['healthy_star']
                item['delicious_star'] = delicious_star if delicious_star != 0 else item['delicious_star']
                item['beauty_star'] = beauty_star if beauty_star != 0 else item['beauty_star']
                break
        else:
            friends_stars.append(
                {
                    "from_openId": from_openId,
                    "healthy_star": healthy_star,
                    "delicious_star": delicious_star,
                    "beauty_star": beauty_star,
                 }
            )

        healthy_stars = [item['healthy_star'] for item in friends_stars if item['healthy_star'] != 0]
        delicious_stars = [item['delicious_star'] for item in friends_stars if item['delicious_star'] != 0]
        beauty_stars = [item['beauty_star'] for item in friends_stars if item['beauty_star'] != 0]
        self.healthy_star = self.cal_star(healthy_stars)
        self.delicious_star = self.cal_star(delicious_stars)
        self.beauty_star = self.cal_star(beauty_stars)
        self.friends_stars = json.dumps(friends_stars)
        self.save()
        return self

    @classmethod
    def cal_star(cls, stars):
        if len(stars) == 0:
            return 0
        star = int(sum(stars)/len(stars) * 10)
        return star
