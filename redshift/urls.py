from django.urls import path

from redshift import views

app_name = 'redshift'

urlpatterns = [
    path('cluster/refresh/'                          , views.refresh_clusters           , name = 'refresh_clusters'),
    path('snapshot/refresh/'                         , views.refresh_snapshots          , name = 'refresh_snapshots'),
    path('table/refresh/'                            , views.refresh_tables             , name = 'refresh_tables'),
    path('queryhistory/refresh_query_history/'       , views.refresh_query_history      , name = 'refresh_query_history'),
    path('queryhistory/vacuum/'                      , views.vacuum                     , name = 'vacuum'),
    path('launch_restore_table_task/<int:task_id>/'  , views.launch_restore_table_task  , name = 'launch_restore_table_task'),
    path('launch_restore_cluster_task/<int:task_id>/', views.launch_restore_cluster_task, name = 'launch_restore_cluster_task'),
    path('download_sql/<int:task_id>/'               , views.download_sql               , name = 'download_sql'),
    path('batch_download_sql/'                       , views.batch_download_sql         , name = 'batch_download_sql'),
]
