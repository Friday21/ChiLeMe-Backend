import json
from datetime import datetime, timedelta

from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class DinnerView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DinnerView, self).dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        dinners = Dinners.objects.filter(user_openId=openId).order_by('-createdAt').all()
        result = [dinner.to_json() for dinner in dinners]
        return JsonResponse(data={'data': result, 'code': 0})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        user_openId = body.get('user_openId')
        org_file_id = body.get('file_id')
        location = body.get('location')
        pic_url = body.get('pic_url', "")
        if not all([user_openId, org_file_id, location]):
            return JsonResponse({'code': 400, 'msg': "参数不合法"})
        dinner_type = "早餐"
        current = datetime.now() + timedelta(hours=8)
        now = current.hour
        if 0 <= now <= 4 or now > 22:
            dinner_type = "夜宵"
        elif 4 < now < 10:
            dinner_type = "早餐"
        elif 10 < now <= 11:
            dinner_type = "早午饭"
        elif 11 < now <= 14:
            dinner_type = "午饭"
        elif 14 < now < 17:
            dinner_type = "下午茶"
        elif 17 <= now <= 22:
            dinner_type = "晚饭"
        dinner = Dinners(user_openId=user_openId,
                         org_file_id=org_file_id,
                         location=location,
                         date=current.date(),
                         createdAt=current,
                         type=dinner_type,
                         pic_url=pic_url)
        dinner.save()
        return JsonResponse(data={'code': 0, 'data': dinner.to_json()})
