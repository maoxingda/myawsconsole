from django.urls import path

from doris import views

app_name = 'doris'

urlpatterns = [
    path('s3/load/<int:task_id>/start/'    , views.start_s3_load_task         , name = 'start_s3_load_task'),
    path('s3/load/<int:task_id>/progress/' , views.query_progress_s3_load_task, name = 'query_progress_s3_load_task'),
    path('refresh/tables/'                 , views.refresh_table_list         , name = 'refresh_table_list'),
    path('create/task/<int:table_id>/'     , views.create_task                , name = 'create_task'),
    path('query/columns/<int:task_id>/'    , views.query_columns              , name = 'query_columns'),
    path('refresh/doris/dbs/<int:task_id>/', views.refresh_doris_db           , name = 'refresh_doris_db'),
    path('routineload/refresh/'            , views.routineload_refresh        , name = 'routineload_refresh'),
    path('routineload/<int:pk>/resume/'    , views.routineload_resume         , name = 'routineload_resume'),
    path('routineload/<int:pk>/recreate/'  , views.routineload_recreate       , name = 'routineload_recreate'),
]
