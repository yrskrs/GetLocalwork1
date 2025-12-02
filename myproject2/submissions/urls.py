from django.urls import path
from . import views

urlpatterns = [
    path('', views.submission_create, name='submission_create'),
    path('success/', views.submission_success, name='submission_success'),
    path('teacher/', views.teacher_login, name='teacher_login'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('teacher/student/<str:student_name>/', views.student_detail, name='student_detail'),
    path('teacher/export/', views.export_grades, name='export_grades'),
    path('teacher/gradebook/', views.gradebook, name='gradebook'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('teacher/comment/<int:submission_id>/', views.update_comment, name='update_comment'),
    path('teacher/view-file/<int:submission_id>/', views.view_file, name='view_file'),
    path('teacher/activity/', views.activity_log, name='activity_log'),
]

