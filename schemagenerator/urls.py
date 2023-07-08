from django.urls import path

from schemagenerator import views

app_name = 'schemagenerator'

urlpatterns = [
    path('table/db/<int:conn_id>/tables/', views.db_tables, name='db_tables'),
    path('task/<int:task_id>/update_table_mappings/', views.update_table_mappings, name='update_table_mappings'),
    path('task/<int:task_id>/launch/', views.launch_task, name='launch_task'),
    path('task/<int:task_id>/download_sql/', views.download_sql, name='download_sql'),
    path('task/<int:task_id>/create_ddl_sql/', views.create_ddl_sql, name='create_ddl_sql'),
]
