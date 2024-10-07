import textwrap

from django.db import models
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.shortcuts import reverse
from django.template import Template, Context

import json


def format_item(item):
    content = textwrap.dedent("""
        {% load date_format %}
        <pre>
            <table>
                <tr>
                    <th>属性</th>
                    <th>数据</th>
                </tr>
                {% for attr, val in content.items %}
                <tr>
                    <td>{{ attr }}</td>
                    <td>{{ val | date_format }}</td>
                </tr>
                {% endfor %}
            </table>
        </pre>
    """)

    context = Context({"content": item})

    content = Template(content).render(context)

    return mark_safe(content)


class Order(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '订单'

    order_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.order_rn

    @admin.display(description='内容')
    def content_format(self):
        return format_item(self.content)


class MainTransaction(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '主交易'

    main_transaction_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.main_transaction_rn

    @admin.display(description='内容')
    def content_format(self):
        return format_item(self.content)


class AccountTransaction(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '账户交易'

    main_transaction_rn = models.CharField(max_length=100)
    account_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.account_rn

    @admin.display(description='内容')
    def content_format(self):
        return format_item(self.content)


class AccountTransactionDetail(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '账户交易详情'

    account_transaction_detail_rn = models.CharField(max_length=100)
    content = models.JSONField(default=dict)

    def __str__(self):
        return self.account_transaction_detail_rn

    @admin.display(description='内容')
    def content_format(self):
        return format_item(self.content)
