from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=30, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    gpa = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    phone = models.CharField(max_length=15, blank=True)
    skills = models.TextField(blank=True, help_text='Comma-separated skills')
    resume = models.FileField(upload_to='resumes/')
    year_of_passing = models.IntegerField(default=2025)
    is_placed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]


class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name


class JobPosting(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.TextField(blank=True, help_text='Comma-separated skills')
    package_lpa = models.FloatField(help_text='Package in LPA')
    min_gpa = models.FloatField(default=6.0, validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    eligible_branches = models.ManyToManyField(Branch, blank=True)
    interview_date = models.DateField()
    application_deadline = models.DateTimeField()
    openings = models.IntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.company_name} — {self.title}"

    def required_skills_list(self):
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    # Inside class JobPosting(models.Model):
    def is_student_eligible(self, student_profile):
    # 1. Check CGPA requirement
        if student_profile.gpa < self.min_gpa:
            return False

    # 2. Check Branch requirement
    # If no branches are specified, assume all are eligible
        if self.eligible_branches.exists():
        # Check if the student's branch ID is in the allowed branches
            if not self.eligible_branches.filter(id=student_profile.branch.id).exists():
                return False

        return True

class Application(models.Model):
    STAGE_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('written_test', 'Written Test'),
        ('gd', 'Group Discussion'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Round'),
        ('placed', 'Placed'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Auto-Withdrawn (Placed Elsewhere)'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'job')

    def __str__(self):
        return f"{self.student} → {self.job} [{self.stage}]"

    def stage_index(self):
        stages = ['applied', 'shortlisted','written_test','gd', 'technical', 'hr', 'placed']
        return stages.index(self.stage) if self.stage in stages else -1


# ─────────────────────────────────────────────
# FEATURE 1: INTERVIEW SCHEDULE
# ─────────────────────────────────────────────
class InterviewSchedule(models.Model):
    ROUND_CHOICES = [
        ('written_test', 'Written Test'),
        ('gd', 'Group Discussion'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Round'),
    ]

    # Links this schedule directly to a specific student's application
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    round_type = models.CharField(max_length=20, choices=ROUND_CHOICES)
    scheduled_at = models.DateTimeField()
    meeting_link = models.URLField(blank=True, null=True, help_text="Optional: For virtual interviews")
    room_location = models.CharField(max_length=200, blank=True, null=True, help_text="Optional: For offline interviews")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"{self.application.student.user.get_full_name()} - {self.get_round_type_display()}"

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='schedules')
    round_type = models.CharField(max_length=20, choices=ROUND_CHOICES)
    date_time = models.DateTimeField()
    mode = models.CharField(max_length=25, choices=ROUND_CHOICES)
    venue_or_link = models.CharField(max_length=300)
    candidates = models.ManyToManyField(StudentProfile, blank=True, related_name='scheduled_interviews')

    def __str__(self):
        return f"{self.job} — {self.get_round_type_display()} on {self.date_time.date()}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif for {self.recipient.username}: {self.message[:40]}"
