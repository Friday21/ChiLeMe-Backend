from collections import defaultdict

from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import UserNotes

Date_Format = "%Y-%m-%d"


class UserNotesHistoryView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UserNotesHistoryView, self).dispatch(request, *args, **kwargs)

    # 获取用户历史记录， 按天倒序排序， 每天的记录汇总求平均。
    def get(self, request, openId, *args, **kwargs):
        user_notes = UserNotes.objects.filter(user_openId=openId).order_by('-date').all()
        result = []
        date_history = defaultdict(list)
        for note in user_notes:
            date_history[note.date].append(note)
        for date_, notes in date_history.items():
            positive = int(sum([note.positive for note in notes]) / len(notes))
            category = {note.category for note in notes}
            result.append({
                "date": date_.strftime("%Y-%m-%d"),
                "positive": positive,
                "category": category,
            })
        return JsonResponse(data={'data': result, 'code': 0})
