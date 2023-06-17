from django.urls import path

from schemagenerator import views

app_name = 'schemagenerator'

urlpatterns = [
    path('table/db/<int:conn_id>/tables/', views.db_tables, name='db_tables'),
    path('table/db/<int:conn_id>/ajax_tables/', views.db_ajax_tables, name='db_ajax_tables'),
    path('task/<int:task_id>/launch/', views.launch_task, name='launch_task'),
    path('task/<int:task_id>/download_sql/', views.download_sql, name='download_sql'),
]
