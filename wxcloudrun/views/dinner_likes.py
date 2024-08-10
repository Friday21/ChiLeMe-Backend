from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class DinnerLikeView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DinnerLikeView, self).dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        dinners = Dinners.objects.filter(user_openId=openId).order_by('-createdAt').all()
        result = [dinner.to_json() for dinner in dinners]
        return JsonResponse(data={'data': result, 'code': 0})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        from_openId = body.get('from_openId')
        dinner_id = body.get('dinner_id')
        healthy_star = body.get('healthy_star', 0)
        delicious_star = body.get('delicious_star', 0)
        beauty_star = body.get('beauty_star', 0)
        if not all([from_openId, dinner_id]):
            return JsonResponse({'code': 400, 'msg': "参数不合法"})

        dinner = Dinners.objects.filter(id=dinner_id).first()
        if not dinner:
            return JsonResponse(data={'code': -1, 'msg': "dinner找不到"})
        new_dinner = dinner.update_start(from_openId, healthy_star, delicious_star, beauty_star)
        if from_openId == dinner.user_openId:
            return JsonResponse(data={'code': 0, 'data': new_dinner.to_self_json()})
        return JsonResponse(data={'code': 0, 'data': new_dinner.to_friend_json(from_openId)})

    def delete(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        from_openId = body.get('from_openId')
        dinner_id = body.get('dinner_id')
        if not all([from_openId, dinner_id]):
            return JsonResponse({'code': 400, 'msg': "参数不合法"})
        dinner = Dinners.objects.filter(id=dinner_id).first()
        if not dinner:
            return JsonResponse({'code': 404, 'msg': "dinner不存在"})
        new_dinner = dinner.delete_star(from_openId)
        if from_openId == dinner.user_openId:
            return JsonResponse(data={'code': 0, 'data': new_dinner.to_self_json()})
        return JsonResponse(data={'code': 0, 'data': new_dinner.to_friend_json(from_openId)})
