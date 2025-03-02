from django.urls import path

from dynamodb import views

app_name = "dynamodb"

urlpatterns = [
    path("order/list/refresh/", views.order_list_refresh, name="order_list_refresh"),
    path("order/list/search/", views.order_search, name="order_search"),
    path(
        "main_transaction/list/refresh/",
        views.main_transaction_list_refresh,
        name="main_transaction_list_refresh",
    ),
    path(
        "main_transaction/list/search/",
        views.main_transaction_search,
        name="main_transaction_search",
    ),
    path(
        "account_transaction/list/search/",
        views.account_transaction_search,
        name="account_transaction_search",
    ),
    path(
        "account_transaction_detail/list/search/",
        views.account_transaction_detail_search,
        name="account_transaction_detail_search",
    ),
]
