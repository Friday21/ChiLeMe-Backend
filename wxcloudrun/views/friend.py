import json
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class FriendView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(FriendView, self).dispatch(request, *args, **kwargs)

    # 获取friends 列表
    def get(self, request, openId, *args, **kwargs):
        user = Users.objects.filter(open_id=openId).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': "用户{}不存在".format(openId)})
        return JsonResponse(data={'data': user.to_json(), 'code': 0})

    # 添加friend
    def post(self, request, openId, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        friend_openId = body.get('friend_openId')

        user1 = Users.objects.filter(open_id=openId).first()
        user2 = Users.objects.filter(open_id=friend_openId).first()
        if not user1 or not user2:
            return JsonResponse({'code': 400, 'msg': "用户不存在"})
        user1.add_friend(user2)
        user2.add_friend(user1)

        return JsonResponse(data={'code': 0, 'data': user1.to_json()})

    # 解除好友关系
    def delete(self, request, openId, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        friend_openId = body.get('friend_openId')
        user1 = Users.objects.filter(open_id=openId).first()
        user2 = Users.objects.filter(open_id=friend_openId).first()
        if not user1 or not user2:
            return JsonResponse({'code': 400, 'msg': "用户不存在"})
        user1.remove_friend(user2)
        user2.remove_friend(user1)
        return JsonResponse(data={'code': 0, 'data': user1.to_json()})
