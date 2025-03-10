import json
from datetime import date, datetime, timedelta
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
            date_ = (datetime.now() + timedelta(hours=8)).date()
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
        fileId = body.get('fileId', '')
        text = body.get('text', '')
        if not fileId and not text:
            return JsonResponse(data={'code': 1, 'msg': '参数错误'})
        if fileId:
            download_url = Users.get_url(fileId)
            try:
                text = recognize_from_url(user_openId, download_url)
            except Exception as e:
                print(e)
                return JsonResponse(data={'code': 0, 'data': UserNotes.to_fake_json()})

        t2 = time()
        print('recognize from url to text cost: {} seconds'.format(int(t2 - t1)))
        try:
            (category, positive, comment) = chat_with_assistant(text)
            positive = int(positive.strip())
        except Exception as e:
            print('chat_with_assistant error: {}'.format(e))
            (category, positive, comment) = ('未识别', 3, "继续加油")
        print('chat_with_assistant cost: {} seconds'.format(int(time() - t2)))
        _date = (datetime.now() + timedelta(hours=8)).date()
        user_note = UserNotes(text=text, category=category, positive=positive, date=_date,
                              user_openId=user_openId, comment=comment)
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
