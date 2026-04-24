from django.contrib import admin
from .models import Branch, StudentProfile, CompanyProfile, JobPosting, Application, InterviewSchedule, Notification

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'branch', 'gpa', 'is_placed')
    search_fields = ('roll_number', 'user__first_name', 'user__last_name')
    list_filter = ('is_placed', 'branch')

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'industry', 'is_verified')
    list_filter = ('is_verified', 'industry')
    search_fields = ('company_name',)

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'package_lpa', 'status', 'application_deadline')
    list_filter = ('status', 'company')
    search_fields = ('title', 'company__company_name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'stage', 'updated_at')
    list_filter = ('stage',)

@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ('job', 'round_type', 'date_time', 'mode')
    list_filter = ('mode', 'round_type')

# Basic registrations for simpler models
admin.site.register(Branch)
admin.site.register(Notification)