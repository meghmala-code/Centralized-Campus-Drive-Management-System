from django.shortcuts import render

def home(request):
    return render(request, 'portal/home.html')

def login_view(request):
    return render(request, 'portal/login.html')

# --- Registration Pages ---
def register_student(request):
    return render(request, 'portal/register_student.html')

def register_hr(request):
    return render(request, 'portal/register_hr.html')

# --- Student Portal ---
def student_dashboard(request):
    return render(request, 'portal/student_dashboard.html')

def student_profile(request):
    return render(request, 'portal/student_profile.html')

def drives_list(request):
    return render(request, 'portal/drives_list.html')

def my_status(request):
    return render(request, 'portal/my_status.html')

# --- HR / Recruiter Portal ---
def hr_dashboard(request):
    return render(request, 'portal/hr_dashboard.html')

def post_job(request):
    return render(request, 'portal/post_job.html')

def candidates(request):
    return render(request, 'portal/candidates.html')

def schedule_interview(request):
    return render(request, 'portal/schedule_interview.html')

def update_status(request):
    return render(request, 'portal/update_status.html')

# --- Admin Portal ---
def admin_dashboard(request):
    return render(request, 'portal/admin_dashboard.html')

def admin_students(request):
    return render(request, 'portal/admin_students.html')

def admin_companies(request):
    return render(request, 'portal/admin_companies.html')

def admin_reports(request):
    return render(request, 'portal/admin_reports.html')
# Create your views here.
