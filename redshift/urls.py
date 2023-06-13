from django.urls import path

from redshift import views

app_name = 'redshift'

urlpatterns = [
    path('refresh/clusters/', views.refresh_clusters, name='refresh_clusters'),
    path('refresh/snapshots/', views.refresh_snapshots, name='refresh_snapshots'),
    path('refresh/tables/', views.refresh_tables, name='refresh_tables'),
    path('launch_restore_table_task/<int:task_id>/', views.launch_restore_table_task, name='launch_restore_table_task'),
    path('launch_restore_cluster_task/<int:task_id>/', views.launch_restore_cluster_task, name='launch_restore_cluster_task'),
]
