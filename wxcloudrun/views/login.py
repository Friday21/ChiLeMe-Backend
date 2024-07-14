import os

import requests
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class LoginView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        code = body.get('code')
        if not code:
            return JsonResponse({'code': 400, 'msg': "参数不合法"})

        # 这些应当从环境变量或配置文件中获取而不是硬编码在代码里
        APP_ID = os.environ.get("APPID")
        APP_SECRET = os.environ.get("APP_SECRET")

        url = f'https://api.weixin.qq.com/sns/jscode2session?appid={APP_ID}&secret={APP_SECRET}&js_code={code}&grant_type=authorization_code'
        response = requests.get(url)
        if response.status_code != 200:
            return JsonResponse({'code': 500, 'msg': "获取open id报错， error: {}".format(response.json())})
        data = response.json()
        open_id = data['openId']
        userInfo = Users.objects.filter(open_id=open_id).first()
        data = {
            "openId": open_id,
            "sessionId": data["session_key"],
            "userInfo": userInfo.to_json() if userInfo else None,
        }

        return JsonResponse(data={'code': 0, 'data': data})
