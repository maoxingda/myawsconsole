from django.db import models
from django.utils.safestring import mark_safe
from django.shortcuts import reverse
from django.contrib import admin


class Topic(models.Model):
    class Meta:
        verbose_name = '主题'
        verbose_name_plural = '主题'
        ordering = ('name',)

    name = models.CharField('名称', max_length=128, unique=True)
    start_time = models.DateTimeField('开始时间', null=True, blank=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    event_time_field_name = models.CharField('事件时间字段名', max_length=128, default='event_time')
    topn = models.IntegerField('TOP N', default=5)
    key = models.CharField('键', max_length=128, default='id')
    has_data = models.BooleanField('是否有数据', default=False, editable=False)
    start_offset = models.BigIntegerField('开始offset', default=0, editable=False)

    def __str__(self):
        return self.name

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        url = reverse('msk:topic_last_message', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=sync-data">最近1条消息</a>')

        url = reverse('msk:topic_message_count', args=(self.pk,))
        buttons.append(f'<a href="{url}">消息数量</a>')

        url = reverse('msk:topic_message_out_of_order_upbound', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=out-of-order-upbound">消息乱序上限</a>')

        url = reverse('msk:topic_message_out_of_order_upbound', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=key-out-of-order-upbound">键消息乱序上限</a>')

        url = reverse('msk:topic_message_out_of_order_upbound', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=sync-data">同步数据</a>')

        url = reverse('msk:topic_message_out_of_order_upbound', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=sync-data-one-day">同步最近1天数据</a>')

        url = reverse('msk:check_message_order', args=(self.pk,))
        buttons.append(f'<a href="{url}?action=sync-data">校验消息顺序</a>')

        return mark_safe('&emsp;&emsp;'.join(buttons))
