"""
time_tracker.py — 浏览时间追踪模型

数据流：
  本地电脑定时任务
    → POST /api/time/upload/<openId>/  (原始 item 数组)
    → 服务端去重 + 写入 TimeItem
    → GET API 实时聚合后返回给小程序
"""

import logging
from urllib.parse import urlparse

from django.db import models

logger = logging.getLogger('log')


def extract_domain(detail: str) -> str:
    """
    从 URL 或 App 名提取主域名。
    例：
      https://claude.ai/chat/abc  →  claude.ai
      www.github.com/foo          →  github.com
      微信                         →  微信
    """
    detail = (detail or '').strip()
    if not detail:
        return ''

    if '://' in detail or detail.startswith('//'):
        try:
            host = urlparse(detail).netloc
        except Exception:
            host = detail.split('/')[0]
    elif '/' in detail and '.' in detail.split('/')[0]:
        # bare domain/path, e.g. "github.com/foo"
        host = detail.split('/')[0]
    else:
        # App 名称 or 无法解析，原样返回
        return detail

    # 去掉 www.
    if host.lower().startswith('www.'):
        host = host[4:]

    return host.lower()


class TimeItem(models.Model):
    """
    每条浏览/使用记录（原始粒度）

    上传 JSON 字段：
      category         – 分类，如 "工具"
      title            – 页面标题或域名，如 "www.google.com"
      start            – ISO 8601，含时区，如 "2026-04-18T12:19:00+08:00"
      duration_seconds – 耗时（秒）
      detail           – 完整 URL 或 App 名
      source           – 来源，如 "browser" / "app"

    去重键：(user_open_id, start_time, detail)
    同一条记录再次上传时，若 duration 有变化则更新，否则跳过。
    """
    user_open_id = models.CharField(max_length=256, db_index=True)

    # 记录所属日期（UTC+8），从 start_time 提取，方便按天查询
    record_date  = models.DateField(db_index=True)

    # 开始时间：去掉时区信息后以 UTC+8 naive datetime 存储
    start_time   = models.DateTimeField()

    duration     = models.IntegerField(default=0)               # 耗时，单位：秒
    category     = models.CharField(max_length=64, default='其他')
    title        = models.CharField(max_length=512, default='')  # 页面标题
    detail       = models.CharField(max_length=2048)             # 完整 URL 或 App 名
    domain       = models.CharField(max_length=256, db_index=True)  # 提取的主域名
    source       = models.CharField(max_length=64, default='browser')  # browser / app / ...

    createdAt    = models.DateTimeField(auto_now_add=True)
    updatedAt    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'TimeItem'
        # 去重：同一用户同一开始时间同一地址，只存一条
        unique_together = ('user_open_id', 'start_time', 'detail')
        ordering        = ['start_time']

    def __str__(self):
        return f'TimeItem({self.user_open_id}, {self.record_date}, {self.domain}, {self.duration}s)'


class TimeInsight(models.Model):
    """
    每人每天的 AI 洞察文字（可选，由本地任务上传）
    重复上传会覆盖。
    """
    user_open_id = models.CharField(max_length=256, db_index=True)
    record_date  = models.DateField()
    insight      = models.TextField(default='')

    createdAt    = models.DateTimeField(auto_now_add=True)
    updatedAt    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'TimeInsight'
        unique_together = ('user_open_id', 'record_date')

    def __str__(self):
        return f'TimeInsight({self.user_open_id}, {self.record_date})'
