from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    # Registration
    path('register/student/', views.register_student, name='register_student'),
    path('register/hr/', views.register_hr, name='register_hr'),

    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/drives/', views.drives_list, name='drives_list'),
    path('student/status/', views.my_status, name='my_status'),

    # HR URLs
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/post-job/', views.post_job, name='post_job'),
    path('hr/candidates/', views.candidates, name='hr_candidates'),
    path('hr/schedule/', views.schedule_interview, name='schedule_interview'),
    path('hr/update-status/', views.update_status, name='update_application_status'),

    # Admin URLs
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/students/', views.admin_students, name='admin_students'),
    path('admin-panel/companies/', views.admin_companies, name='admin_companies'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
]