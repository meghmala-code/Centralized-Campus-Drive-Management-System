from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    StudentProfile, CompanyProfile, JobPosting,
    Application, InterviewSchedule, Notification, Branch
)
from .forms import (
    StudentRegistrationForm, HRRegistrationForm,
    StudentProfileForm, JobPostingForm,
    ApplicationStatusForm, InterviewScheduleForm
)

# ─── Helpers ───────────────────────────────────────────────────────────────

def get_role(user):
    if user.groups.filter(name='HR').exists():
        return 'hr'
    if user.groups.filter(name='Student').exists():
        return 'student'
    if user.is_staff:
        return 'admin'
    return None

def notify(user, message):
    Notification.objects.create(recipient=user, message=message)

# ─── Public & Auth ─────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'portal/home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'portal/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            group, _ = Group.objects.get_or_create(name='Student')
            user.groups.add(group)
            StudentProfile.objects.create(
                user=user,
                roll_number=form.cleaned_data['roll_number'],
                gpa=0.0
            )
            login(request, user)
            messages.success(request, 'Account created! Please complete your profile.')
            return redirect('student_profile')
    else:
        form = StudentRegistrationForm()
    return render(request, 'portal/register_student.html', {'form': form})

def register_hr(request):
    if request.method == 'POST':
        form = HRRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            group, _ = Group.objects.get_or_create(name='HR')
            user.groups.add(group)
            CompanyProfile.objects.create(
                user=user,
                company_name=form.cleaned_data['company_name'],
                industry=form.cleaned_data['industry'],
            )
            login(request, user)
            messages.success(request, 'HR account created! Pending admin verification.')
            return redirect('hr_dashboard')
    else:
        form = HRRegistrationForm()
    return render(request, 'portal/register_hr.html', {'form': form})

# ─── Dashboard Router ──────────────────────────────────────────────────────

@login_required
def dashboard(request):
    role = get_role(request.user)
    if role == 'admin':
        return redirect('admin_dashboard')
    if role == 'student':
        return redirect('student_dashboard')
    if role == 'hr':
        return redirect('hr_dashboard')
    return redirect('login')

# ─── Admin Views ───────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    total_students = StudentProfile.objects.count()
    total_companies = CompanyProfile.objects.count()
    placed = StudentProfile.objects.filter(is_placed=True).count()
    active_drives = JobPosting.objects.filter(status='active').count()
    recent_drives = JobPosting.objects.order_by('-created_at')[:5]
    branches = Branch.objects.all()
    branch_stats = []
    for b in branches:
        total = StudentProfile.objects.filter(branch=b).count()
        p = StudentProfile.objects.filter(branch=b, is_placed=True).count()
        branch_stats.append({'branch': b, 'total': total, 'placed': p,
                              'pct': round(p / total * 100) if total else 0})
    ctx = {
        'total_students': total_students,
        'total_companies': total_companies,
        'placed': placed,
        'unplaced': total_students - placed,
        'placement_pct': round(placed / total_students * 100) if total_students else 0,
        'active_drives': active_drives,
        'recent_drives': recent_drives,
        'branch_stats': branch_stats,
    }
    return render(request, 'portal/admin_dashboard.html', ctx)

@login_required
def admin_students(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    q = request.GET.get('q', '')
    students = StudentProfile.objects.select_related('user', 'branch')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(roll_number__icontains=q)
        )
    return render(request, 'portal/admin_students.html', {'students': students, 'q': q})

@login_required
def admin_companies(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    companies = CompanyProfile.objects.select_related('user')
    return render(request, 'portal/admin_companies.html', {'companies': companies})

@login_required
def verify_company(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    company = get_object_or_404(CompanyProfile, pk=pk)
    company.is_verified = True
    company.save()
    notify(company.user, f'Your company "{company.company_name}" has been verified by the admin.')
    messages.success(request, f'{company.company_name} verified.')
    return redirect('admin_companies')

@login_required
def admin_reports(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    students = StudentProfile.objects.count()
    placed = StudentProfile.objects.filter(is_placed=True).count()
    offers = Application.objects.filter(stage='placed').count()
    companies = CompanyProfile.objects.filter(is_verified=True).count()
    top_companies = (
        JobPosting.objects.filter(status='closed')
        .values('company__company_name')
        .annotate(offers=Count('applications', filter=Q(applications__stage='placed')))
        .order_by('-offers')[:6]
    )
    ctx = {
        'students': students, 'placed': placed, 'unplaced': students - placed,
        'placement_pct': round(placed / students * 100) if students else 0,
        'offers': offers, 'companies': companies,
        'top_companies': top_companies,
    }
    return render(request, 'portal/admin_reports.html', ctx)

@login_required
def schedule_interview(request, job_pk):
    # Restricted strictly to admin as per our workflow design
    if not request.user.is_staff:
        return redirect('dashboard')
    job = get_object_or_404(JobPosting, pk=job_pk)
    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.job = job
            schedule.save()
            form.save_m2m()
            for student in schedule.candidates.all():
                notify(student.user,
                       f'Interview scheduled for {job.title}: {schedule.get_round_type_display()} on '
                       f'{schedule.date_time.strftime("%d %b %Y %I:%M %p")} — {schedule.venue_or_link}')
            messages.success(request, 'Interview scheduled and students notified.')
            return redirect('admin_dashboard') # Returns admin to their dashboard
    else:
        form = InterviewScheduleForm()
    return render(request, 'portal/schedule_interview.html', {'form': form, 'job': job})

# ─── Student Views ─────────────────────────────────────────────────────────

@login_required
def student_dashboard(request):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
        
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = profile.applications.select_related('job', 'job__company').order_by('-applied_at')
    all_drives = JobPosting.objects.filter(status='active')
    
    # Filter the jobs the student is actually eligible for
    eligible_jobs = [d for d in all_drives if d.is_student_eligible(profile)]
    
    # Calculate the dynamic stats for the top cards
    total_applied = applications.count()
    shortlisted = applications.filter(stage__in=['written_test', 'technical', 'hr']).count()
    upcoming_interviews = applications.filter(stage__in=['technical', 'hr']).count()
    
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    
    ctx = {
        'profile': profile,
        'applications': applications,
        'total_applied': total_applied,
        'shortlisted': shortlisted,
        'upcoming_interviews': upcoming_interviews,
        'available_jobs': eligible_jobs,  # THIS is what connects to our HTML table!
        'notifications': notifications,
    }
    return render(request, 'portal/student_dashboard.html', ctx)

@login_required
def student_profile(request):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
        
    # Safely grabs the profile, or silently creates a blank one if missing!
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    jobs = JobPosting.objects.filter(status='active').select_related('company')
    
    if request.method == 'POST':
        # This handles the "Save" button click
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        
        print("\n=== DID THE FILE ARRIVE? ===", request.FILES, "\n")
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_profile')
        else:
            # DEBUGGING: If the form fails, print the exact reason to your terminal!
            print("FORM ERRORS:", form.errors)
            
    else:
        # THE MISSING PIECE! This handles just visiting the page (GET request)
        form = StudentProfileForm(instance=profile)
        
    return render(request, 'portal/student_profile.html', {'form': form, 'profile': profile})

@login_required
def drives_list(request):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
        
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # We will call this 'jobs' to keep it simple
    jobs = JobPosting.objects.filter(status='active').select_related('company')
    
    # DEBUG: This will print in your terminal so we can see if Django thinks you have a resume
    print(f"DEBUG: Student {request.user.username} has resume: {bool(profile.resume)}")
    
    return render(request, 'portal/drives_list.html', {
        'jobs': jobs, 
        'profile': profile  # This is the key that unlocks the buttons!
    })

@login_required
def apply_drive(request, pk):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
    profile = get_object_or_404(StudentProfile, user=request.user)
    job = get_object_or_404(JobPosting, pk=pk, status='active')
    if not job.is_student_eligible(profile):
        messages.error(request, 'You are not eligible for this drive.')
        return redirect('drives_list')
    app, created = Application.objects.get_or_create(student=profile, job=job)
    if created:
        notify(request.user, f'You have successfully applied for {job.title} at {job.company.company_name}.')
        notify(job.company.user, f'{profile.user.get_full_name()} applied for {job.title}.')
        messages.success(request, f'Applied to {job.title} successfully!')
    else:
        messages.info(request, 'You have already applied for this drive.')
    return redirect('drives_list')

@login_required
def my_status(request):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = profile.applications.select_related('job', 'job__company').order_by('-updated_at')
    stages = ['applied', 'written_test', 'technical', 'hr', 'placed']
    return render(request, 'portal/my_status.html', {
        'applications': applications,
        'stages': stages,
    })

# ─── HR Views ──────────────────────────────────────────────────────────────

@login_required
def hr_dashboard(request):
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
    company = get_object_or_404(CompanyProfile, user=request.user)
    jobs = company.job_postings.annotate(applicant_count=Count('applications'))
    total_applicants = Application.objects.filter(job__company=company).count()
    shortlisted = Application.objects.filter(job__company=company, stage='written_test').count()
    offers = Application.objects.filter(job__company=company, stage='placed').count()
    ctx = {
        'company': company,
        'jobs': jobs,
        'total_applicants': total_applicants,
        'shortlisted': shortlisted,
        'offers': offers,
    }
    return render(request, 'portal/hr_dashboard.html', ctx)

@login_required
def post_job(request):
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
    company = get_object_or_404(CompanyProfile, user=request.user)
    if not company.is_verified:
        messages.error(request, 'Your company is pending admin verification.')
        return redirect('hr_dashboard')
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            form.save_m2m()
            messages.success(request, 'Job posted successfully!')
            return redirect('hr_dashboard')
    else:
        form = JobPostingForm()
    return render(request, 'portal/post_job.html', {'form': form})

@login_required
def hr_candidates(request, job_pk):
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
    company = get_object_or_404(CompanyProfile, user=request.user)
    job = get_object_or_404(JobPosting, pk=job_pk, company=company)
    applications = job.applications.select_related('student', 'student__user', 'student__branch')
    return render(request, 'portal/candidates.html', {'job': job, 'applications': applications})

@login_required
def update_application_status(request, pk):
    # Security: Ensure only HR can access this
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
        
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {application.student.user.get_full_name()}'s status.")
            return redirect('hr_candidates', job_pk=application.job.id)
    else:
        form = ApplicationStatusForm(instance=application)
        
    return render(request, 'portal/update_status.html', {
        'form': form, 
        'application': application
    })

@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))