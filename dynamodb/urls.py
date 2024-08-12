from django.urls import path

from dynamodb import views

app_name = 'dynamodb'

urlpatterns = [
    path('order/list/refresh/'   , views.order_list_refresh, name = 'order_list_refresh'),
    path('order/<int:pk>/format/', views.order_format      , name = 'order_format'),
    path('order/list/search/'    , views.order_search      , name = 'order_search'),

    path('main_transaction/list/refresh/'   , views.main_transaction_list_refresh, name = 'main_transaction_list_refresh'),
    path('main_transaction/<int:pk>/format/', views.main_transaction_format      , name = 'main_transaction_format'),
    path('main_transaction/list/search/'    , views.main_transaction_search      , name = 'main_transaction_search'),
]
