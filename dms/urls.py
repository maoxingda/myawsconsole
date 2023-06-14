from django.urls import path

from dms import views

app_name = 'dms'

urlpatterns = [
    path('task/refresh/', views.refresh_tasks, name='refresh_tasks'),
    path('endpoint/refresh/', views.refresh_endpoints, name='refresh_endpoints'),
]
