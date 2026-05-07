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
    if user.is_anonymous:
        return None
    
    # Check if the user belongs to a specific group
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return 'admin'
    
    if user.groups.filter(name='hr').exists():
        return 'hr'
    
    # If they have a profile but no special group, they are a student
    if user.groups.filter(name__iexact='student').exists() or hasattr(user, 'studentprofile'):
        return 'student'
        
    return None # Default fallback

def notify(user, message):
    Notification.objects.create(recipient=user, message=message)

# ─── Public & Auth ─────────────────────────────────────────────────────────

def home_view(request):
    if request.user.is_authenticated:
        # If logged in, send them to their specific dashboard
        return redirect('dashboard')
    else:
        # If not logged in, send them to the login page
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
    return redirect('home')

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
            group, _ = Group.objects.get_or_create(name='hr')
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
    if not request.user.is_authenticated:
        return redirect('home')
    role = get_role(request.user)
    if role == 'admin':
        return redirect('admin_dashboard')
    if role == 'student':
        return redirect('student_dashboard')
    if role == 'hr':
        return redirect('hr_dashboard')
    else:
        # 1. Check if they have the HR group, but their CompanyProfile is missing
        if request.user.groups.filter(name__iexact='hr').exists():
            dynamic_error = "Your HR account is registered, but your Company Profile data is missing or corrupted."
            
        # 2. Check if they have absolutely no groups and no profiles at all
        elif not request.user.groups.exists() and not hasattr(request.user, 'studentprofile'):
            dynamic_error = "Your account has no assigned role. It looks like your registration was interrupted."
            
        # 3. Catch-all for weird database ghosts (like our uppercase 'HR' bug)
        else:
            # This grabs whatever weird group they belong to and shows it to them
            group_names = ", ".join([g.name for g in request.user.groups.all()])
            if group_names:
                dynamic_error = f"Unrecognized permission group detected: '{group_names}'. Please contact an administrator."
            else:
                dynamic_error = "Critical account configuration error. Please contact support."

        # Log them out and show the specific dynamic error
        logout(request)
        messages.error(request, dynamic_error)
        return redirect('login')

# ─── Admin Views ───────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if get_role(request.user) != 'admin':
        return redirect('dashboard')
        
    # High-level analytics for the Placement Head
    total_students = StudentProfile.objects.count()
    total_companies = User.objects.filter(groups__name='hr').count() # Or your HR logic
    total_jobs = JobPosting.objects.count()
    total_placed = Application.objects.filter(stage='placed').count()
    
    # Recent activity
    recent_placements = Application.objects.filter(stage='placed').order_by('-updated_at')[:5]
    active_drives = JobPosting.objects.filter(status='active').order_by('-created_at')[:5]
    
    ctx = {
    'total_students': StudentProfile.objects.count(),
    'total_companies': User.objects.filter(groups__name='hr').count(),
    'total_placed': Application.objects.filter(stage='placed').count(),
    'active_drives': JobPosting.objects.filter(status='active').count(),
    'placement_perc': 71.4, # Or your calculation
    'recent_jobs': JobPosting.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'portal/admin_dashboard.html', ctx)

@login_required
def admin_students(request):
    # Ensure only Admin/TPO can view this
    if get_role(request.user) != 'admin':
        return redirect('dashboard')
        
    # Fetch all student profiles, grabbing the associated User data to be fast
    students = StudentProfile.objects.select_related('user').all().order_by('-gpa')
    
    return render(request, 'portal/admin_students.html', {'students': students})

@login_required
def admin_companies(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    companies = CompanyProfile.objects.select_related('user').all()
    
    # THIS IS THE FIX: Using is_verified instead of status
    verified_count = companies.filter(is_verified=True).count()
    pending_count = companies.filter(is_verified=False).count()
    
    context = {
        'companies': companies,
        'verified_count': verified_count,
        'pending_count': pending_count,
    }
    
    return render(request, 'portal/admin_companies.html', context)

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

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def admin_reports(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    # Basic student stats
    total_students = StudentProfile.objects.count()
    total_placed = StudentProfile.objects.filter(is_placed=True).count()
    total_unplaced = total_students - total_placed
    
    # Safely calculate percentages to avoid dividing by zero
    if total_students > 0:
        placement_perc = (total_placed / total_students) * 100
    else:
        placement_perc = 0
    
    unplaced_perc = 100 - placement_perc

    # THE BULLETPROOF FIX: Query forwards from Application up to Company!
    top_recruiters_data = Application.objects.filter(stage='placed').values(
        'job__company__company_name'
    ).annotate(
        offers_count=Count('id')
    ).order_by('-offers_count')[:5]

    # Convert the raw database dictionary into a format the HTML template expects
    top_recruiters = [
        {
            'company_name': item['job__company__company_name'], 
            'offers_count': item['offers_count']
        }
        for item in top_recruiters_data
    ]

    context = {
        'total_students': total_students,
        'total_placed': total_placed,
        'total_unplaced': total_unplaced,
        'placement_perc': placement_perc,
        'unplaced_perc': unplaced_perc,
        'top_recruiters': top_recruiters,
    }
    
    return render(request, 'portal/admin_reports.html', context)

@login_required
def schedule_interview(request, job_id):
    job = get_object_or_404(JobPosting, pk=job_id)
    active_apps = Application.objects.filter(job=job).exclude(stage__in=['applied', 'rejected', 'placed'])

    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST)
        if form.is_valid():
            round_type = form.cleaned_data['round_type']
            scheduled_at = form.cleaned_data['scheduled_at']
            meeting_link = form.cleaned_data['meeting_link']
            room_location = form.cleaned_data['room_location']
            notes = form.cleaned_data['notes']

            schedules_to_create = []
            
            for app in active_apps:
                # 1. Prepare the schedule object
                schedule = InterviewSchedule(
                    job=job,
                    application=app,
                    round_type=round_type,
                    scheduled_at=scheduled_at,
                    date_time=scheduled_at,      # <--- THE MAGIC FIX: Satisfies the old database column!
                    meeting_link=meeting_link,
                    room_location=room_location,
                    notes=notes
                )
                schedules_to_create.append(schedule)
                
                # 2. Update their application stage
                app.stage = round_type
                
                # 3. NOTIFY THE STUDENT
                alert_msg = f"Your {schedule.get_round_type_display()} has been scheduled for {scheduled_at.strftime('%d %b %Y %I:%M %p')}."
                notify(app.student.user, alert_msg)

            # Bulk save to the database for performance
            if schedules_to_create:
                InterviewSchedule.objects.bulk_create(schedules_to_create)
                Application.objects.bulk_update(active_apps, ['stage'])

            messages.success(request, f"✅ Successfully scheduled {round_type} and notified {active_apps.count()} candidates!")
            return redirect('admin_drive_candidates', job_id=job.id)
    else:
        form = InterviewScheduleForm()

    context = {
        'form': form,
        'job': job,
        'candidate_count': active_apps.count()
    }
    return render(request, 'portal/schedule_interview.html', context)

@login_required
def admin_company_detail(request, company_id):
    """Shows the company details and all the job drives they are hosting."""
    company = get_object_or_404(CompanyProfile, pk=company_id)
    
    # Changed Job to JobPosting
    jobs = JobPosting.objects.filter(company=company).order_by('-created_at')

    context = {
        'company': company,
        'jobs': jobs
    }
    return render(request, 'portal/admin_company_detail.html', context)



@login_required
def admin_drive_candidates(request, job_id):
    job = get_object_or_404(JobPosting, pk=job_id)
    
    # --- 1. HANDLE BULK ACTIONS (POST) ---
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('selected_candidates')
        
        if action and selected_ids:
            apps_to_update = Application.objects.filter(id__in=selected_ids, job=job)
            
            if action == 'reject':
                apps_to_update.update(stage='rejected')
                messages.error(request, f"Bulk Action: {apps_to_update.count()} candidates rejected.")
            elif action == 'placed':
                apps_to_update.update(stage='placed')
                # Note: This is where you'd trigger the Conflict Management to withdraw them from other drives!
                # 2. CONFLICT MANAGEMENT: Get the IDs of the students who just got placed
                student_ids_placed = apps_to_update.values_list('student_id', flat=True)
                # 3. Find all their OTHER active applications and auto-withdraw them
                other_active_apps = Application.objects.filter(
                    student_id__in=student_ids_placed
                ).exclude(
                    job=job  # Don't touch the job they just got
                ).exclude(
                    stage__in=['rejected', 'placed', 'withdrawn'] # Don't touch already finished pipelines
                )
                
                # Count how many collateral applications we are closing
                collateral_count = other_active_apps.count()
                
                # Execute the withdrawal
                other_active_apps.update(stage='withdrawn')

                messages.success(request, f"🌟 {apps_to_update.count()} candidates placed! {collateral_count} competing applications were auto-withdrawn.")
                
            
            elif action == 'reset':
                apps_to_update.update(stage='applied')
                messages.info(request, f"Bulk Action: {apps_to_update.count()} candidates reset to Applied stage.")
            else:
                # This automatically handles shortlisted, written, gd, technical, hr, and placed!
                apps_to_update.update(stage=action)
                messages.success(request, f"Bulk Action: {apps_to_update.count()} candidates moved to {action.upper()} stage!")
            
            return redirect('admin_drive_candidates', job_id=job.id)

    # --- 2. HANDLE FILTERING (GET) ---
    applications = Application.objects.filter(job=job).select_related('student__user')

    search_query = request.GET.get('search', '')
    filter_branch = request.GET.get('branch', '')
    filter_stage = request.GET.get('stage', '')
    filter_min_gpa = request.GET.get('min_gpa', '')

    if search_query:
        applications = applications.filter(
            Q(student__user__first_name__icontains=search_query) | 
            Q(student__user__last_name__icontains=search_query)
        )
    if filter_branch:
        applications = applications.filter(Q(student__branch__name__icontains=filter_branch) | 
            Q(student__branch__code__icontains=filter_branch))
    if filter_stage:
        applications = applications.filter(stage=filter_stage)
    if filter_min_gpa:
        try:
            applications = applications.filter(student__gpa__gte=float(filter_min_gpa))
        except ValueError:
            pass

    context = {
        'job': job,
        'applications': applications,
        'current_search': search_query,
        'current_branch': filter_branch,
        'current_stage': filter_stage,
        'current_gpa': filter_min_gpa,
    }
    return render(request, 'portal/admin_drive_candidates.html', context)


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

    # This finds any active job where the deadline has passed, and instantly shuts it down.
    JobPosting.objects.filter(status='active', application_deadline__lt=timezone.now()).update(status='closed')
    
    # We will call this 'jobs' to keep it simple
    jobs = JobPosting.objects.filter(status='active').select_related('company')
    
    # --- 2. THE PROACTIVE GATEKEEPER (UI FLAG) ---
    is_already_placed = Application.objects.filter(student=profile, stage='placed').exists()
    active_apps_count = Application.objects.filter(student=profile).exclude(stage__in=['rejected', 'withdrawn']).count()

    has_reached_limit = active_apps_count >= 3

    # DEBUG: This will print in your terminal so we can see if Django thinks you have a resume
    print(f"DEBUG: Student {request.user.username} has resume: {bool(profile.resume)}")
    print(f"DEBUG: Student is already placed: {is_already_placed}")
    
    return render(request, 'portal/drives_list.html', {
        'jobs': jobs, 
        'profile': profile,
        'is_already_placed': is_already_placed,  # <-- This unlocks the UI lock
        'has_reached_limit': has_reached_limit,
        'active_apps_count': active_apps_count
    })

@login_required
def apply_drive(request, pk):
    if get_role(request.user) != 'student':
        return redirect('dashboard')
        
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # --- 1. THE PROACTIVE GATEKEEPER (BACKEND LOCK) ---
    is_already_placed = Application.objects.filter(student=profile, stage='placed').exists()
    
    if is_already_placed:
        messages.error(request, "Conflict Management: You are already placed and cannot apply for new drives.")
        return redirect('drives_list')
    
    # --- GATEKEEPER 2: The "3 Active Drives" Limit ---
    # Count applications that are NOT in a finished state (rejected or withdrawn)
    active_apps_count = Application.objects.filter(student=profile).exclude(stage__in=['rejected', 'withdrawn']).count()
    
    if active_apps_count >= 3:
        messages.warning(request, "Application Limit Reached: You already have 3 active applications. You must wait for a result before applying to more.")
        return redirect('drives_list')
        
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
    
    # I went ahead and added 'gd' to this list to match your updated model!
    stages = ['applied','shortlisted', 'written_test', 'gd', 'technical', 'hr', 'placed'] 
    
    # ---> FETCH THE NOTIFICATIONS <---
    # Grabs the 5 most recent notifications for this specific student
    notifications = Notification.objects.filter(recipient=request.user).order_by('-id')[:5]
    # ---------------------------------

    return render(request, 'portal/my_status.html', {
        'applications': applications,
        'stages': stages,
        'notifications': notifications, # Pass the variable to the HTML template
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
def update_application_status(request, app_pk):
    # Security: Ensure only HR can access this
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
        
    application = get_object_or_404(Application, pk=app_pk)
    
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            updated_app = form.save()
            
            # 2. ---> TRIGGER THE NOTIFICATION <---
            student_user = updated_app.student.user
            company_name = updated_app.job.company.company_name
            new_stage = updated_app.get_stage_display() # Gets the readable text (e.g., "Shortlisted")
            
            alert_msg = f"Status Update: Your application for {company_name} has been moved to '{new_stage}'."
            notify(student_user, alert_msg)


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

# Make sure you have imported your notify function at the top!

@login_required
def quick_update_status(request, app_pk, action):
    # Security check
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
        
    application = get_object_or_404(Application, pk=app_pk)
    student_name = application.student.user.get_full_name()
    company_name = application.job.company.company_name
    
    # Process the quick action
    if action == 'shortlist':
        application.stage = 'shortlisted'
        messages.success(request, f"✅ {student_name} has been shortlisted!")
        notify(application.student.user, f"Great news! Your profile has been shortlisted for {company_name}. Next step: Written Test.")
        
    elif action == 'reject':
        application.stage = 'rejected'
        messages.warning(request, f"❌ {student_name} was rejected.")
        # Optional: You can choose not to notify students of rejections right away to soften the blow
        # notify(application.student.user, f"Update: Your application for {company_name} was not selected to move forward.")
        
    application.save()
    
    # Instantly redirect back to the candidate list
    return redirect('hr_candidates', job_pk=application.job.id)

@login_required
def edit_job(request, pk):
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
        
    company = get_object_or_404(CompanyProfile, user=request.user)
    job = get_object_or_404(JobPosting, pk=pk, company=company)
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job "{job.title}" updated successfully!')
            return redirect('hr_dashboard')
    else:
        form = JobPostingForm(instance=job)
        
    return render(request, 'portal/edit_job.html', {'form': form, 'job': job})

@login_required
def delete_job(request, pk):
    if get_role(request.user) != 'hr':
        return redirect('dashboard')
        
    company = get_object_or_404(CompanyProfile, user=request.user)
    job = get_object_or_404(JobPosting, pk=pk, company=company)
    
    if request.method == 'POST':
        # --- THE TWO-STEP DELETION LOGIC ---
        if job.status != 'closed':
            # Step 1: Soft Delete (Close the drive)
            job.status = 'closed'
            job.save()
            messages.warning(request, f'Drive "{job.title}" is now CLOSED. Clicking delete again will permanently erase it.')
        else:
            # Step 2: Hard Delete (Permanent Purge)
            title = job.title
            job.delete() # Destroys the job and cascades to delete all applications
            messages.success(request, f'Drive "{title}" and all related data have been permanently deleted.')
            
        return redirect('hr_dashboard')
        
    return render(request, 'portal/confirm_delete_job.html', {'job': job})