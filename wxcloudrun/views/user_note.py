import json
from datetime import date, datetime
from time import time

from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.utils import recognize_from_url,chat_with_assistant
from wxcloudrun.models import UserNotes, Users

Date_Format = "%Y-%m-%d"

class UserNotesView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UserNotesView, self).dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        date_str = request.GET.get('date')
        if date_str:
            date_ = datetime.strptime(date_str, Date_Format).date()
        else:
            date_ = date.today()
        user_notes = UserNotes.objects.filter(user_openId=openId, date=date_).order_by('-createdAt').all()
        result = [note.to_json() for note in user_notes]

        return JsonResponse(data={'data': result, 'code': 0})

    # 声音转语音， 并调用LLM分析分类、情绪
    def post(self, request, openId, *args, **kwargs):
        t1 = time()
        print()
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        user_openId = body.get('user_openId')
        fileId = body.get('fileId')
        download_url = Users.get_url(fileId)
        text = recognize_from_url(user_openId, download_url)
        t2 = time()
        print('recognize from url to text cost: {} seconds'.format(t2 - t1))
        (category, positive) = chat_with_assistant(text)
        print('chat_with_assistant cost: {} seconds'.format(time() - t2))
        positive = int(positive)
        user_note = UserNotes(text=text, category=category, positive=positive, date=date.today(), user_openId=user_openId)
        user_note.save()
        return JsonResponse(data={'code': 0, 'data': user_note.to_json()})

    def put(self, request, openId, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        user_note_id = body.get('id')
        user_note = UserNotes.objects.get(id=user_note_id)
        if user_note.user_openId != openId:
            return JsonResponse(data={'code': 1, 'msg': '无权限'})
        user_note.category = body.get('category')
        user_note.positive = body.get('positive')
        user_note.save()
        return JsonResponse(data={'code': 0, 'data': user_note.to_json()})

    def delete(self, request, openId, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        user_note_id = body.get('id')
        user_note = UserNotes.objects.get(id=user_note_id)
        if user_note.user_openId != openId:
            return JsonResponse(data={'code': 1, 'msg': '无权限'})
        user_note.delete()
        return JsonResponse(data={'code': 0, 'data': user_note.to_json()})
