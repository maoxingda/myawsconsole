from django.urls import path

from dms import views

app_name = 'dms'

urlpatterns = [
    path('task/refresh/', views.refresh_tasks, name='refresh_tasks'),
    path('table/refresh/<int:task_id>/', views.refresh_tables, name='refresh_tables'),
    path('endpoint/refresh/', views.refresh_endpoints, name='refresh_endpoints'),
]
