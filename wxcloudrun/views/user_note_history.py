from collections import defaultdict, Counter

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
            # 统计 category 出现次数
            category_counts = Counter(note.category for note in notes)

            # 找到出现最多的 category
            max_count = max(category_counts.values())
            most_frequent_categories = [cat for cat, count in category_counts.items() if count == max_count]

            # 找到最接近 positive 的 category
            best_category = min(
                most_frequent_categories,
                key=lambda cat: abs(
                    positive - sum(note.positive for note in notes if note.category == cat))
            )
            result.append({
                "date": date_.strftime("%Y-%m-%d"),
                "positive": positive,
                "category": best_category,
            })
        return JsonResponse(data={'data': result, 'code': 0})
