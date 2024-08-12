from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.utils.safestring import mark_safe

from utils.sql import execute_sql, TargetDatabase
from utils.dynamodb import batch_get_item
from dynamodb import models

import os
import json

limit = 1


def order_list_refresh(request):
    sql = f"select order_rn from middle.middle_order order by create_time desc limit {limit}"
    rows = execute_sql(sql, TargetDatabase.DORIS, True)
    keys = [
        row['order_rn'] for row in rows
    ]

    for item in batch_get_item('bi-oltp-order', 'order_rn', keys):
        models.Order(order_rn=item['order_rn'], content=item).save()

    return redirect(reverse('admin:dynamodb_order_changelist'))


def order_search(request):
    term = request.GET.get('term')

    if len(term.strip()) > 0:
        for item in batch_get_item('bi-oltp-order', 'order_rn', [term]):
            models.Order(order_rn=item['order_rn'], content=item).save()

    return redirect(reverse('admin:dynamodb_order_changelist'))


def main_transaction_list_refresh(request):
    sql = f"select main_transaction_rn from middle.middle_main_transaction order by transaction_time desc limit {limit}"
    rows = execute_sql(sql, TargetDatabase.DORIS, True)
    keys = [
        row['main_transaction_rn'] for row in rows
    ]

    for item in batch_get_item('bi-oltp-main_transaction', 'main_transaction_rn', keys):
        models.MainTransaction(main_transaction_rn=item['main_transaction_rn'], content=item).save()

    return redirect(reverse('admin:dynamodb_maintransaction_changelist'))


def main_transaction_search(request):
    term = request.GET.get('term')

    if len(term.strip()) > 0:
        for item in batch_get_item('bi-oltp-main_transaction', 'main_transaction_rn', [term]):
            models.MainTransaction(main_transaction_rn=item['main_transaction_rn'], content=item).save()

    return redirect(reverse('admin:dynamodb_maintransaction_changelist'))
