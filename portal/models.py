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
    application_deadline = models.DateField()
    openings = models.IntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.company_name} — {self.title}"

    def required_skills_list(self):
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    # Inside class JobPosting(models.Model):
    def is_student_eligible(self, student_profile):
    # Check CGPA
        if student_profile.gpa < self.min_gpa:
            return False
    # Check Branch
        if self.eligible_branches.all() and student_profile.branch not in [b.name for b in self.eligible_branches.all()]:
            return False
        return True

class Application(models.Model):
    STAGE_CHOICES = [
        ('applied', 'Applied'),
        ('written_test', 'Written Test'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Round'),
        ('placed', 'Placed'),
        ('rejected', 'Rejected'),
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
        stages = ['applied', 'written_test', 'technical', 'hr', 'placed']
        return stages.index(self.stage) if self.stage in stages else -1


class InterviewSchedule(models.Model):
    MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'In-Person'),
    ]
    ROUND_CHOICES = [
        ('written', 'Written Test'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Round'),
        ('gd', 'Group Discussion'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='schedules')
    round_type = models.CharField(max_length=20, choices=ROUND_CHOICES)
    date_time = models.DateTimeField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
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
