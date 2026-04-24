from django.urls import path
from . import views

urlpatterns = [
    # ─── Global & Auth ──────────────────────────────────────────────
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'), # The smart router
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    # ─── Registration ───────────────────────────────────────────────
    path('register/student/', views.register_student, name='register_student'),
    path('register/hr/', views.register_hr, name='register_hr'),

    # ─── Student URLs ───────────────────────────────────────────────
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/drives/', views.drives_list, name='drives_list'),
    path('student/drives/<int:pk>/apply/', views.apply_drive, name='apply_drive'), # Dynamic ID
    path('student/status/', views.my_status, name='my_status'),

    # ─── HR URLs ────────────────────────────────────────────────────
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/post-job/', views.post_job, name='post_job'),
    path('hr/job/<int:job_pk>/candidates/', views.hr_candidates, name='hr_candidates'), # Dynamic ID
    path('hr/application/<int:app_pk>/update/', views.update_application_status, name='update_application_status'), # Dynamic ID

    # ─── Admin URLs ─────────────────────────────────────────────────
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/students/', views.admin_students, name='admin_students'),
    path('admin-panel/companies/', views.admin_companies, name='admin_companies'),
    path('admin-panel/companies/<int:pk>/verify/', views.verify_company, name='verify_company'), # Dynamic ID
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/job/<int:job_pk>/schedule/', views.schedule_interview, name='schedule_interview'), # Dynamic ID
]