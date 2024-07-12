from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import *


class DinnerView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DinnerView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        dinners = Dinners.objects.order_by('-date').all()
        result = [dinner.to_json() for dinner in dinners]
        return JsonResponse(data={'data': result, 'code': 0})

    def post(self, request):
        user_openId = request.POST.get('user_openId')
        org_file_id = request.POST.get('file_id')
        location = request.POST.get('location')
        pic_url = request.POST.get('pic_url', "")
        if not all([user_openId, org_file_id, location]):
            return JsonResponse({'code': 400, 'msg': "参数不合法"})

        dinner = Dinners(user_openId=user_openId,
                         org_file_id=org_file_id,
                         location=location,
                         pic_url=pic_url)
        dinner.save()
        return JsonResponse(data={'code': 0, 'data': dinner.to_json()})
