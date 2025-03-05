from collections import defaultdict
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils.timezone import now
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models import UserNotes

Date_Format = "%Y-%m-%d"


class UserNotesReportView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UserNotesReportView, self).dispatch(request, *args, **kwargs)

    # 获取用户历史记录， 按天倒序排序， 每天的记录汇总求平均。
    def get(self, request, openId, *args, **kwargs):
        result = {
            "weekData": 0,
            "monthData": 0,
            "yearData": [0] * 12,
            "weekpercentage": "0%",
            "monthpercentage": "0%",
            "weekGoodDay": 2,
            "monthGoodDay": 2,
            "yearGoodDay": 2,
        }

        # 获取当前时间
        current_date = now().date()
        current_year = current_date.year
        first_day_of_year = datetime(current_year, 1, 1).date()

        user_notes = UserNotes.objects.filter(user_openId=openId, date__gte=first_day_of_year).order_by('-date').all()
        # 记录每天是否为“不虚度”
        date_history = defaultdict(list)
        for note in user_notes:
            date_history[note.date].append(note.category)

        # 统计不虚度的天数
        weekGoodDay = 0
        monthGoodDay = 0
        yearGoodDays = [0] * 12  # 每个月的不虚度天数
        first_day_of_week = current_date - timedelta(days=current_date.weekday())  # 计算当前周的第一天
        first_day_of_month = current_date.replace(day=1)  # 计算当前月的第一天

        for date_, categories in date_history.items():
            if any(category > 3 for category in categories):  # 如果这一天有任意一个 category > 3，则算作“不虚度”
                if date_ >= first_day_of_week:
                    weekGoodDay += 1
                if date_ >= first_day_of_month:
                    monthGoodDay += 1
                if date_.year == current_year:
                    yearGoodDays[date_.month - 1] += 1  # 统计每个月的不虚度天数

        # 计算不虚度百分比
        weekpercentage = int((weekGoodDay / 7) * 100)
        month_days = (current_date - first_day_of_month).days + 1
        monthpercentage = int((monthGoodDay / month_days) * 100)

        # 计算全年每个月的不虚度百分比
        yearData = [int((good_days / 30) * 100) if good_days > 0 else 0 for good_days in yearGoodDays]

        # 构造返回结果
        result = {
            "weekData": weekpercentage,
            "monthData": monthpercentage,
            "yearData": yearData,
            "weekpercentage": f"{weekpercentage}%",
            "monthpercentage": f"{monthpercentage}%",
            "weekGoodDay": weekGoodDay,
            "monthGoodDay": monthGoodDay,
            "yearGoodDay": sum(yearGoodDays),
        }

        return JsonResponse(data={'data': result, 'code': 0})
