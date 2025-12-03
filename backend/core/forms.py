from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from datetime import date
from .models import Leave, User, Project, ProjectMember, TimesheetEntry


class LeaveApplicationForm(forms.ModelForm):
    """
    Form for employees to apply for leave with validations.
    """
    
    class Meta:
        model = Leave
        fields = ['leave_type', 'from_date', 'to_date', 'reason']
        widgets = {
            'from_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'to_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'leave_type': forms.Select(
                attrs={
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'reason': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Please provide reason for leave...',
                    'class': 'form-textarea w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['from_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')
        self.fields['to_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')
    
    def clean_from_date(self):
        """Validate that from_date is not in the past."""
        from_date = self.cleaned_data.get('from_date')
        if from_date and from_date < date.today():
            raise ValidationError("Leave start date cannot be in the past.")
        return from_date
    
    def clean_to_date(self):
        """Validate that to_date is not before from_date."""
        to_date = self.cleaned_data.get('to_date')
        from_date = self.cleaned_data.get('from_date')
        
        if to_date and to_date < date.today():
            raise ValidationError("Leave end date cannot be in the past.")
        
        if from_date and to_date and to_date < from_date:
            raise ValidationError("End date cannot be before start date.")
        
        return to_date
    
    def clean(self):
        """Validate that there are no overlapping leaves."""
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        leave_type = cleaned_data.get('leave_type')
        
        if not (from_date and to_date and self.user):
            return cleaned_data
        
        # Check for overlapping leaves
        overlapping_leaves = Leave.objects.filter(
            employee=self.user,
            status__in=['PENDING', 'APPROVED'],
            from_date__lte=to_date,
            to_date__gte=from_date
        )
        
        # Exclude current instance if editing
        if self.instance.pk:
            overlapping_leaves = overlapping_leaves.exclude(pk=self.instance.pk)
        
        if overlapping_leaves.exists():
            overlapping_leave = overlapping_leaves.first()
            raise ValidationError(
                f"You already have a {overlapping_leave.get_leave_type_display().lower()} "
                f"from {overlapping_leave.from_date} to {overlapping_leave.to_date} "
                f"that overlaps with this request."
            )
        
        # Check leave balance
        if self.user and hasattr(self.user, 'employeeprofile'):
            profile = self.user.employeeprofile
            duration_days = (to_date - from_date).days + 1
            
            # Get current year's approved leaves for this type
            current_year_leaves = Leave.objects.filter(
                employee=self.user,
                leave_type=leave_type,
                status='APPROVED',
                from_date__year=from_date.year
            )
            
            # Exclude current instance if editing
            if self.instance.pk:
                current_year_leaves = current_year_leaves.exclude(pk=self.instance.pk)
            
            used_days = sum(leave.duration_days for leave in current_year_leaves)
            
            # Check balance based on leave type
            balance_field_map = {
                'ANNUAL': profile.annual_leaves,
                'SICK': profile.sick_leaves,
                'MATERNITY': profile.maternity_leaves,
                'PATERNITY': profile.paternity_leaves,
                'EMERGENCY': profile.emergency_leaves,
                'COMPENSATORY': profile.compensatory_leaves,
            }
            
            if leave_type in balance_field_map:
                available_balance = balance_field_map[leave_type] - used_days
                if duration_days > available_balance:
                    raise ValidationError(
                        f"Insufficient {leave_type.lower()} leave balance. "
                        f"You have {available_balance} days remaining, but requested {duration_days} days."
                    )
        
        return cleaned_data


class ProjectForm(forms.ModelForm):
    """
    Form for creating and editing projects.
    """
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'manager', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Enter project name'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-textarea w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Enter project description'
                }
            ),
            'manager': forms.Select(
                attrs={
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'start_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter managers to only show users with manager, HR, or admin roles
        self.fields['manager'].queryset = User.objects.filter(
            role__in=['MANAGER', 'HR', 'ADMIN']
        ).order_by('first_name', 'last_name')
        
        # Add empty option
        self.fields['manager'].empty_label = "Select Project Manager"
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date.")
        
        return cleaned_data


class ProjectMemberForm(forms.ModelForm):
    """
    Form for adding/editing project members.
    """
    
    class Meta:
        model = ProjectMember
        fields = ['employee', 'role']
        widgets = {
            'employee': forms.Select(
                attrs={
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'role': forms.TextInput(
                attrs={
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'e.g., Developer, Designer, Tester'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Filter out users who are already members of this project
        if self.project:
            existing_members = ProjectMember.objects.filter(
                project=self.project
            ).values_list('employee_id', flat=True)
            
            self.fields['employee'].queryset = User.objects.exclude(
                id__in=existing_members
            ).filter(is_active=True).order_by('first_name', 'last_name')
        else:
            self.fields['employee'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')
        
        # Add empty option
        self.fields['employee'].empty_label = "Select Employee"


class ProjectMemberEditForm(forms.ModelForm):
    """
    Form for editing existing project member roles.
    """
    
    class Meta:
        model = ProjectMember
        fields = ['role']
        widgets = {
            'role': forms.TextInput(
                attrs={
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'e.g., Developer, Designer, Tester'
                }
            ),
        }


class TimesheetEntryForm(forms.ModelForm):
    """
    Form for employees to submit daily timesheet entries.
    """
    
    class Meta:
        model = TimesheetEntry
        fields = ['date', 'project', 'hours', 'description']
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'project': forms.Select(
                attrs={
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'hours': forms.NumberInput(
                attrs={
                    'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'step': '0.25',
                    'min': '0.25',
                    'max': '24',
                    'placeholder': 'e.g., 8.0'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-textarea w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Brief description of work performed...'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
        
        # Filter projects to only show projects where the user is a member or manager
        if self.user:
            user_projects = Project.objects.filter(
                models.Q(projectmember__employee=self.user) |
                models.Q(manager=self.user)
            ).distinct().order_by('name')
            
            self.fields['project'].queryset = user_projects
            self.fields['project'].empty_label = "Select Project (Optional)"
        
        # Set max date to today (prevent future entries)
        self.fields['date'].widget.attrs['max'] = date.today().strftime('%Y-%m-%d')
    
    def clean_date(self):
        entry_date = self.cleaned_data.get('date')
        if entry_date and entry_date > date.today():
            raise ValidationError("Cannot create timesheet entries for future dates.")
        return entry_date
    
    def clean_hours(self):
        hours = self.cleaned_data.get('hours')
        if hours and hours > 24:
            raise ValidationError("Hours cannot exceed 24 per day.")
        if hours and hours <= 0:
            raise ValidationError("Hours must be greater than 0.")
        return hours
    
    def clean(self):
        cleaned_data = super().clean()
        employee = self.user
        entry_date = cleaned_data.get('date')
        hours = cleaned_data.get('hours')
        project = cleaned_data.get('project')
        
        if employee and entry_date and hours:
            # Check if entry already exists for this employee, date, and project
            existing_entry = TimesheetEntry.objects.filter(
                employee=employee,
                date=entry_date,
                project=project
            ).exclude(pk=self.instance.pk)
            
            if existing_entry.exists():
                raise ValidationError(
                    f"A timesheet entry already exists for {entry_date} "
                    f"and project '{project.name if project else 'No Project'}'. "
                    "Please edit the existing entry instead."
                )
            
            # Check total hours for the day don't exceed 24
            from django.db.models import Sum
            existing_entries = TimesheetEntry.objects.filter(
                employee=employee,
                date=entry_date
            ).exclude(pk=self.instance.pk)
            
            total_hours = existing_entries.aggregate(
                total=Sum('hours')
            )['total'] or 0
            
            if total_hours + hours > 24:
                raise ValidationError(
                    f"Total hours for {entry_date} would exceed 24. "
                    f"Current total: {total_hours}h, Adding: {hours}h"
                )
        
        return cleaned_data


class TimesheetEntryEditForm(TimesheetEntryForm):
    """
    Form for editing existing timesheet entries.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow editing of existing entries without date restrictions
        if self.instance.pk:
            # Remove max date restriction for editing existing entries
            if 'max' in self.fields['date'].widget.attrs:
                del self.fields['date'].widget.attrs['max']