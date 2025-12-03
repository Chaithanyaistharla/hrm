from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import Leave, User


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