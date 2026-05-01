from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudentProfile, CompanyProfile, JobPosting, Application, InterviewSchedule

# --- Pro-Tip: A helper class to automatically add Bootstrap styling to all forms ---
class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Checkboxes need a different class in Bootstrap
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                pass # Checkbox multiples handle their own styling
            else:
                field.widget.attrs['class'] = 'form-control'
                
            # Keep labels looking clean
            if field.label:
                field.label = field.label.title()

# ─── Auth & Registration Forms ──────────────────────────────────────────────

class StudentRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    roll_number = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        # Removed password1 and password2 (UserCreationForm handles them automatically)
        fields = ['username', 'first_name', 'last_name', 'email']


class HRRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=200, required=True)
    industry = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


# ─── Portal Forms ──────────────────────────────────────────────────────────

class StudentProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['phone', 'gpa', 'branch', 'skills', 'resume', 'year_of_passing']
        widgets = {
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, Java, React (Comma separated)'}),
            'gpa': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '10'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }


class JobPostingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'required_skills',
            'package_lpa', 'min_gpa', 'eligible_branches',
            'interview_date', 'application_deadline', 'openings', 'status'
        ]
        widgets = {
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
            'eligible_branches': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input custom-checkbox-list'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the role and responsibilities...'}),
            'required_skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, DSA, System Design'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ApplicationStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ['stage', 'notes']
        widgets = {
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add feedback or interview notes here...'}),
        }


class InterviewScheduleForm(forms.ModelForm):
    # This widget creates a native browser calendar/clock picker
    scheduled_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )

    class Meta:
        model = InterviewSchedule
        fields = ['round_type', 'scheduled_at', 'meeting_link', 'room_location', 'notes']
        widgets = {
            'round_type': forms.Select(attrs={'class': 'form-select'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/...'}),
            'room_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Block B, Room 302'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Bring your physical resume.'}),
        }