from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class UserView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UserView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        open_id = body.get('open_id')
        avatar_url = body.get('avatar_url')
        alias = body.get('alias')
        if not all([open_id, avatar_url, alias]):
            return JsonResponse({'code': 400, 'msg': "参数不合法"})
        user = Users.objects.filter(open_id=open_id).first()
        if not user:
            user = Users(open_id=open_id)
        user.alias = alias
        user.avatar_url = avatar_url
        user.save()
        return JsonResponse(data={'code': 0, 'data': user.to_json()})
