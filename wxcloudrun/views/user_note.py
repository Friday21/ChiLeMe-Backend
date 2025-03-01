import json
from datetime import date

from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.utils import recognize_from_url,chat_with_assistant
from wxcloudrun.models import UserNotes, Users


class UserNotesView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UserNotesView, self).dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        user_notes = UserNotes.objects.filter(user_openId=openId).order_by('-createdAt')[:100]
        return [note.to_json() for note in user_notes]

    # 声音转语音， 并调用LLM分析分类、情绪
    def post(self, request, openId, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        user_openId = body.get('user_openId')
        fileId = body.get('fileId')
        download_url = Users.get_url(fileId)
        text = recognize_from_url(user_openId, download_url)
        (category, positive) = chat_with_assistant(text)
        positive = int(positive)
        user_note = UserNotes(text=text, category=category, positive=positive, date=date.today(), user_openId=user_openId)
        user_note.save()
        return JsonResponse(data={'code': 0, 'data': user_note.to_json()})

