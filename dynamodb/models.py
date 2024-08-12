from django.db import models
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.shortcuts import reverse

import json


class Order(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '订单'

    order_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.order_rn

    @admin.display(description='内容')
    def content_format(self):
        content = json.dumps(self.content, indent=4, ensure_ascii=False)

        return mark_safe(f'<pre>{content}</pre>')


class MainTransaction(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '主交易'

    main_transaction_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.main_transaction_rn

    @admin.display(description='内容')
    def content_format(self):
        content = json.dumps(self.content, indent=4, ensure_ascii=False)

        return mark_safe(f'<pre>{content}</pre>')
