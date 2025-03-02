from django.urls import path

from dms import views

app_name = "dms"

urlpatterns = [
    path("task/refresh/", views.refresh_tasks, name="refresh_tasks"),
    path(
        "task/full_refresh_tasks/", views.full_refresh_tasks, name="full_refresh_tasks"
    ),
    path(
        "task/<int:task_id>/download_table_mapping/",
        views.download_table_mapping,
        name="download_table_mapping",
    ),
    path(
        "task/<int:task_id>/stop_then_resume_task/",
        views.stop_then_resume_task,
        name="stop_then_resume_task",
    ),
    path("task/<int:task_id>/task_tables/", views.task_tables, name="task_tables"),
    path("table/refresh/<int:task_id>/", views.refresh_tables, name="refresh_tables"),
    path("endpoint/refresh/", views.refresh_endpoints, name="refresh_endpoints"),
]
