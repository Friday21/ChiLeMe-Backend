"""
time_tracker.py — 浏览时间追踪接口

─── 本地电脑上传（定时任务） ───────────────────────────────────────────────
POST /api/time/upload/<openId>/
  Body JSON:
  {
    "apiSecret": "xxx",          # 可选，对应环境变量 TIME_UPLOAD_SECRET
    "insight": "今天...",         # 可选，当日 AI 点评
    "items": [
      {
        "category":         "工具",
        "title":            "www.google.com",
        "start":            "2026-04-18T12:19:00+08:00",
        "duration_seconds": 60,
        "detail":           "https://www.google.com/search?q=codex",
        "source":           "browser",
        "date":             "2026-04-18"        # 可选；若提供则按此归档到对应日期，
                                                # 否则按 start 的日期归档。典型场景：
                                                # 睡眠记录 start 是入睡时刻（可能跨天），
                                                # date 显式指向"属于哪一天的睡眠"。
      },
      ...
    ]
  }

  去重规则：(user_open_id, start_time, detail) 唯一
    - 若已存在且 duration 未变 → skip
    - 若已存在且 duration 有变 → update
    - 若不存在                 → create

─── 小程序读取 ─────────────────────────────────────────────────────────────
GET /api/time/overview/<openId>/?date=YYYY-MM-DD
GET /api/time/week/<openId>/?date=YYYY-MM-DD
GET /api/time/sites/<openId>/?date=YYYY-MM-DD
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone, date as date_type

from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wxcloudrun.models.time_tracker import TimeItem, TimeInsight, extract_domain

logger = logging.getLogger('log')

DATE_FMT     = '%Y-%m-%d'
_CST = timezone(timedelta(hours=8))


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _china_today() -> date_type:
    return datetime.now(_CST).date()


def _parse_date(s: str) -> date_type:
    return datetime.strptime(s, DATE_FMT).date()


def _fmt_date(d: date_type) -> str:
    return d.strftime(DATE_FMT)


def _parse_start_time(s: str) -> datetime:
    """
    解析 start 字段，支持带时区和不带时区的 ISO 8601 格式。
    统一返回 UTC+8 naive datetime（去掉 tzinfo），方便存入 DateTimeField。

    支持：
      2026-04-18T12:19:00+08:00   → naive 2026-04-18 12:19:00
      2026-04-18T12:19:00+00:00   → naive 2026-04-18 20:19:00
      2026-04-18T12:19:00Z        → 同上
      2026-04-18T12:19:00         → 视为 UTC+8，原样 naive 返回
      2026-04-18T12:19:00.123456  → 同上（去掉微秒）
      2026-04-18 12:19:00         → 同上
    """
    s = s.strip().replace('Z', '+00:00')

    # 尝试 fromisoformat（Python 3.7+ 支持 +HH:MM 时区）
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            # 转换到 UTC+8 后去掉时区信息
            return dt.astimezone(_CST).replace(tzinfo=None)
        # 无时区，视为 UTC+8 naive，直接返回（去掉微秒保持整洁）
        return dt.replace(microsecond=0, tzinfo=None)
    except (ValueError, AttributeError):
        pass

    # 降级：逐格式尝试（兼容老格式）
    for fmt in (
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
    ):
        try:
            return datetime.strptime(s, fmt).replace(microsecond=0)
        except ValueError:
            continue

    raise ValueError(f'无法解析时间：{s}')


# ─────────────────────────────────────────────────────────────────────────────
# 聚合辅助
# ─────────────────────────────────────────────────────────────────────────────

def _aggregate(items):
    """
    从 TimeItem QuerySet 聚合出所有展示所需数据。
    返回 dict，供各 GET 接口直接使用。
    """
    # 按分类累计秒数
    cat_seconds   = defaultdict(int)
    # 按域名累计秒数/访问次数/最早开始/最晚结束
    domain_data   = defaultdict(lambda: {
        'seconds': 0, 'visits': 0, 'name': '', 'category': '',
        'start': None, 'end': None,
    })
    # 按小时 + 分类累计秒数（用于时段热力图）
    hourly_cat    = defaultdict(lambda: defaultdict(int))
    # 按日期累计秒数（用于周趋势）
    date_seconds  = defaultdict(int)

    total_seconds = 0

    for item in items:
        sec = item.duration
        total_seconds += sec
        cat_seconds[item.category] += sec

        d = domain_data[item.domain]
        d['seconds']  += sec
        d['visits']   += 1
        # 优先用上传的 title，否则用域名
        d['name']      = d['name'] or (item.title or item.domain)
        d['category']  = item.category

        # 开始/结束时间（同域名多条时取最早入 & 最晚出）
        item_end = item.start_time + timedelta(seconds=sec)
        if d['start'] is None or item.start_time < d['start']:
            d['start'] = item.start_time
        if d['end'] is None or item_end > d['end']:
            d['end'] = item_end

        hour = item.start_time.hour
        hourly_cat[hour][item.category] += sec

        date_seconds[_fmt_date(item.record_date)] += sec

    # 分类列表
    categories = sorted(
        [{'name': k, 'minutes': round(v / 60)} for k, v in cat_seconds.items()],
        key=lambda x: -x['minutes'],
    )

    # 时段结构：{hour: [{catName, minutes}]}
    hourly = {
        str(h): [
            {'catName': cat, 'minutes': round(sec / 60)}
            for cat, sec in sorted(cats.items(), key=lambda x: -x[1])
        ]
        for h, cats in sorted(hourly_cat.items())
    }

    # 网站列表
    sites = sorted(
        [
            {
                'name':      info['name'] or _domain_to_name(dom),
                'domain':    dom,
                'category':  info['category'],
                'minutes':   round(info['seconds'] / 60),
                'visits':    info['visits'],
                'hourly':    _site_hourly(items, dom),
                # ISO 字符串（naive UTC+8）。用于前端展示开始/结束时间点，
                # 典型场景：睡眠记录显示"入睡 23:01 · 起床 05:22"。
                'startTime': info['start'].isoformat() if info['start'] else None,
                'endTime':   info['end'].isoformat()   if info['end']   else None,
            }
            for dom, info in domain_data.items()
        ],
        key=lambda x: -x['minutes'],
    )

    total_minutes = round(total_seconds / 60)
    site_count    = len(domain_data)
    page_count    = sum(d['visits'] for d in domain_data.values())
    avg_minutes   = round(total_minutes / site_count) if site_count else 0

    return {
        'totalMinutes': total_minutes,
        'siteCount':    site_count,
        'pageCount':    page_count,
        'avgMinutes':   avg_minutes,
        'categories':   categories,
        'hourly':       hourly,
        'sites':        sites,
        'dateSeconds':  dict(date_seconds),
    }


def _site_hourly(items, domain: str):
    """计算某域名的逐小时分布"""
    hour_map = defaultdict(int)
    for item in items:
        if item.domain == domain:
            hour_map[item.start_time.hour] += item.duration
    return [
        {'hour': h, 'minutes': round(sec / 60)}
        for h, sec in sorted(hour_map.items())
    ]


# 常见域名 → 中文/英文名称映射（title 缺失时的兜底）
_DOMAIN_NAME_MAP = {
    'claude.ai':              'Claude',
    'github.com':             'GitHub',
    'youtube.com':            'YouTube',
    'weibo.com':              '微博',
    'twitter.com':            'Twitter',
    'x.com':                  'X',
    'sspai.com':              '少数派',
    'google.com':             'Google',
    'taobao.com':             '淘宝',
    'jd.com':                 '京东',
    'zhihu.com':              '知乎',
    'bilibili.com':           'bilibili',
    'v2ex.com':               'V2EX',
    'producthunt.com':        'Product Hunt',
    'news.ycombinator.com':   'Hacker News',
    'stackoverflow.com':      'Stack Overflow',
    'reddit.com':             'Reddit',
    'notion.so':              'Notion',
    'linear.app':             'Linear',
    'figma.com':              'Figma',
}


def _domain_to_name(domain: str) -> str:
    return _DOMAIN_NAME_MAP.get(domain, domain)


# ─────────────────────────────────────────────────────────────────────────────
# 上传接口
# ─────────────────────────────────────────────────────────────────────────────

class TimeUploadView(View):
    """
    POST /api/time/upload/<openId>/

    接收原始 item 数组，服务端去重后写入。
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, openId, *args, **kwargs):
        # ── 解析 Body ──
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'code': 1, 'msg': '请求体 JSON 格式错误'}, status=400)

        # ── 可选鉴权 ──
        secret_env = os.getenv('TIME_UPLOAD_SECRET', '')
        if secret_env and body.get('apiSecret', '') != secret_env:
            return JsonResponse({'code': 403, 'msg': '鉴权失败'}, status=403)

        items_raw = body.get('items', [])
        if not isinstance(items_raw, list) or not items_raw:
            return JsonResponse({'code': 1, 'msg': 'items 不能为空'}, status=400)

        # ── 逐条处理 ──
        created = updated = skipped = errors = 0

        for raw in items_raw:
            try:
                start_str        = raw.get('start', '')
                duration_seconds = int(raw.get('duration_seconds', 0))
                category         = str(raw.get('category', '其他')).strip() or '其他'
                title            = str(raw.get('title', '')).strip()
                detail           = str(raw.get('detail', '')).strip()
                source           = str(raw.get('source', 'browser')).strip() or 'browser'
                date_override    = str(raw.get('date', '')).strip()

                if not start_str or not detail:
                    errors += 1
                    continue

                start_dt    = _parse_start_time(start_str)
                # record_date 优先取显式 date 字段（支持跨天场景，如睡眠记录），
                # 没有就按 start 的日期归档。
                if date_override:
                    try:
                        record_date = _parse_date(date_override)
                    except ValueError:
                        logger.warning(f'[TimeUpload] invalid date field: {date_override}, fallback to start date')
                        record_date = start_dt.date()
                else:
                    record_date = start_dt.date()
                detail      = detail[:500]   # 截取前 500 字符，匹配字段长度
                domain      = extract_domain(detail)

                # 去重逻辑
                existing = TimeItem.objects.filter(
                    user_open_id=openId,
                    start_time=start_dt,
                    detail=detail,
                ).first()

                if existing is None:
                    TimeItem.objects.create(
                        user_open_id=openId,
                        record_date=record_date,
                        start_time=start_dt,
                        duration=duration_seconds,
                        category=category,
                        title=title,
                        detail=detail,
                        domain=domain,
                        source=source,
                    )
                    created += 1
                elif existing.duration != duration_seconds or existing.record_date != record_date:
                    # duration 或 record_date 有变化，更新
                    # （record_date 变化场景：旧数据按 start 归档错了天，再次上传带 date 修正）
                    existing.duration    = duration_seconds
                    existing.record_date = record_date
                    existing.category    = category
                    existing.title       = title
                    existing.source      = source
                    existing.save(update_fields=['duration', 'record_date', 'category', 'title', 'source', 'updatedAt'])
                    updated += 1
                else:
                    skipped += 1

            except Exception as e:
                logger.warning(f'[TimeUpload] item error: {e} | raw={raw}')
                errors += 1

        # ── 可选：保存当日 insight ──
        insight = str(body.get('insight', '')).strip()
        if insight:
            # 允许整条上传请求体里显式指定 insight 的日期（兼容旧调用：无则推导）
            insight_date_str = str(body.get('date', '')).strip()
            target_date = None
            if insight_date_str:
                try:
                    target_date = _parse_date(insight_date_str)
                except ValueError:
                    target_date = None

            if target_date is None:
                # 从 items 中取最晚的日期（优先用每条 item 的 date 字段，没有则用 start）
                dates_in_upload = set()
                for raw in items_raw:
                    try:
                        item_date = str(raw.get('date', '')).strip()
                        if item_date:
                            dates_in_upload.add(_parse_date(item_date))
                        else:
                            dt = _parse_start_time(raw.get('start', ''))
                            dates_in_upload.add(dt.date())
                    except Exception:
                        pass
                target_date = max(dates_in_upload) if dates_in_upload else _china_today()

            TimeInsight.objects.update_or_create(
                user_open_id=openId,
                record_date=target_date,
                defaults={'insight': insight},
            )

        logger.info(
            f'[TimeUpload] {openId} total={len(items_raw)} '
            f'created={created} updated={updated} skipped={skipped} errors={errors}'
        )

        return JsonResponse({
            'code': 0,
            'msg':  '上传成功',
            'data': {
                'total':   len(items_raw),
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'errors':  errors,
            },
        })


# ─────────────────────────────────────────────────────────────────────────────
# 小程序读取接口
# ─────────────────────────────────────────────────────────────────────────────

class TimeOverviewView(View):
    """GET /api/time/overview/<openId>/?date=YYYY-MM-DD"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        date_str = request.GET.get('date', '')
        try:
            target = _parse_date(date_str) if date_str else _china_today()
        except ValueError:
            return JsonResponse({'code': 1, 'msg': 'date 格式错误'}, status=400)

        items = list(TimeItem.objects.filter(user_open_id=openId, record_date=target))
        if not items:
            return JsonResponse({'code': 0, 'data': None})

        agg = _aggregate(items)

        # 与昨天对比
        yesterday    = target - timedelta(days=1)
        yest_items   = TimeItem.objects.filter(user_open_id=openId, record_date=yesterday)
        yest_total   = round(sum(i.duration for i in yest_items) / 60)
        diff_minutes = agg['totalMinutes'] - yest_total

        # 获取 insight
        insight_obj = TimeInsight.objects.filter(
            user_open_id=openId, record_date=target
        ).first()
        insight = insight_obj.insight if insight_obj else ''

        return JsonResponse({
            'code': 0,
            'data': {
                'totalMinutes': agg['totalMinutes'],
                'siteCount':    agg['siteCount'],
                'pageCount':    agg['pageCount'],
                'avgMinutes':   agg['avgMinutes'],
                'diffMinutes':  diff_minutes,
                'categories':   agg['categories'],
                'hourly':       agg['hourly'],
                'insight':      insight,
            },
        })


class TimeWeekView(View):
    """GET /api/time/week/<openId>/?date=YYYY-MM-DD

    返回过去 7 天（含 pivot 当天，往前推 6 天）的日维度数据：
      - totalMinutes：全天总时长
      - categories：各分类时长 dict，{catName: minutes}

    示例：
      {
        'data': [
          {'date': '2026-04-17', 'totalMinutes': 720,
           'categories': {'工作': 420, '学习': 100, '娱乐': 50, '睡眠': 480}},
          ...
        ]
      }
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        date_str = request.GET.get('date', '')
        try:
            pivot = _parse_date(date_str) if date_str else _china_today()
        except ValueError:
            return JsonResponse({'code': 1, 'msg': 'date 格式错误'}, status=400)

        # 过去 7 天：pivot 往前推 6 天（含 pivot 共 7 天）
        week_dates = [pivot - timedelta(days=i) for i in range(6, -1, -1)]
        today      = _china_today()

        # 批量查询这 7 天所有 items
        items = TimeItem.objects.filter(
            user_open_id=openId,
            record_date__gte=week_dates[0],
            record_date__lte=week_dates[-1],
        )

        # 按日期累计 total + 按分类累计
        date_seconds: dict = defaultdict(int)
        date_cat_seconds: dict = defaultdict(lambda: defaultdict(int))
        for item in items:
            dk = _fmt_date(item.record_date)
            date_seconds[dk] += item.duration
            date_cat_seconds[dk][item.category] += item.duration

        data = []
        for d in week_dates:
            dk = _fmt_date(d)
            is_future = d > today
            total_sec = 0 if is_future else date_seconds.get(dk, 0)
            cats_sec  = {} if is_future else date_cat_seconds.get(dk, {})
            data.append({
                'date':         dk,
                'totalMinutes': round(total_sec / 60),
                'categories':   {k: round(v / 60) for k, v in cats_sec.items()},
            })

        return JsonResponse({'code': 0, 'data': data})


class TimeSitesView(View):
    """GET /api/time/sites/<openId>/?date=YYYY-MM-DD"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, openId, *args, **kwargs):
        date_str = request.GET.get('date', '')
        try:
            target = _parse_date(date_str) if date_str else _china_today()
        except ValueError:
            return JsonResponse({'code': 1, 'msg': 'date 格式错误'}, status=400)

        items = list(TimeItem.objects.filter(user_open_id=openId, record_date=target))
        if not items:
            return JsonResponse({'code': 0, 'data': {'totalMinutes': 0, 'categories': [], 'sites': []}})

        agg = _aggregate(items)

        return JsonResponse({
            'code': 0,
            'data': {
                'totalMinutes': agg['totalMinutes'],
                'categories':   agg['categories'],
                'sites':        agg['sites'],
            },
        })
