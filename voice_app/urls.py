from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('job/<uuid:job_id>/', views.job_status, name='job_status'),
    path('job/<uuid:job_id>/result/', views.job_result, name='job_result'),
    path('job/<uuid:job_id>/download/', views.download_file, name='download_file'),
    path('api/job/<uuid:job_id>/status/', views.api_job_status, name='api_job_status'),
    path('jobs/', views.jobs_list, name='jobs_list'),
]
