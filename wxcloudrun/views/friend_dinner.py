import json
from datetime import datetime

from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class FriendDinnerView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(FriendDinnerView, self).dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        user = Users.objects.filter(open_id=openId).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': "参数不合法"})
        friends = json.loads(user.friends)
        friend_dict = dict()
        for friend in friends:
            friend_dict[friend['open_id']] = friend
        open_ids = [friend['open_id'] for friend in friends if friend['open_id'] != openId]
        dinners = Dinners.objects.filter(user_openId__in=open_ids).order_by('-createdAt')[:1000]
        result = []
        for dinner in dinners:
            info = dinner.to_friend_json(openId)
            dinner_user_info = friend_dict[dinner.user_openId]
            info.update(dinner_user_info)
            result.append(info)
        return JsonResponse(data={'data': result, 'code': 0})

