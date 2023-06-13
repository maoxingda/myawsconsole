from django.urls import path

from dms import views

app_name = 'dms'

urlpatterns = [
    path('refresh/tasks/', views.refresh_tasks, name='refresh_tasks'),
    path('refresh/endpoints/', views.refresh_endpoints, name='refresh_endpoints'),
]
