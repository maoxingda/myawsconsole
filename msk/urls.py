from django.urls import path

from msk import views

app_name = 'msk'

urlpatterns = [
    path('topic/list/refresh/'                         , views.refresh_topic_list                , name = 'refresh_topic_list'),
    path('topic/<int:pk>/message_out_of_order_upbound/', views.topic_message_out_of_order_upbound, name = 'topic_message_out_of_order_upbound'),
    path('topic/<int:pk>/message_count/'               , views.topic_message_count               , name = 'topic_message_count'),
    path('topic/<int:pk>/last_message/'                , views.topic_last_message                , name = 'topic_last_message'),
]
