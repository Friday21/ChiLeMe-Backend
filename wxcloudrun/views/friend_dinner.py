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
        dinners = Dinners.objects.exclude(user_openId=openId).exclude(user_openId="").order_by('-createdAt').all()
        result = [dinner.to_friend_json(openId) for dinner in dinners]
        return JsonResponse(data={'data': result, 'code': 0})

