from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Role(models.TextChoices):
    EMPLOYEE = "EMPLOYEE", "Employee"
    MANAGER = "MANAGER", "Manager"
    HR = "HR", "HR"
    ADMIN = "ADMIN", "Admin"


class User(AbstractUser):
    """
    Custom User model extending AbstractUser with role assignment.
    """
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.EMPLOYEE,
        help_text="User's role in the organization"
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique employee identifier"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text="Contact phone number"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department the user belongs to"
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the employee was hired"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the user account is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name() or 'No Name'})"
    
    @property
    def role_name(self):
        """Return the role name or 'No Role' if not assigned."""
        return self.get_role_display() if self.role else 'No Role'
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.role == role_name
    
    def is_hr(self):
        """Check if user is in HR role."""
        return self.has_role(Role.HR)
    
    def is_manager(self):
        """Check if user is a Manager."""
        return self.has_role(Role.MANAGER)
    
    def is_admin_role(self):
        """Check if user is in Admin role (different from Django's is_staff)."""
        return self.has_role(Role.ADMIN)


class EmployeeProfile(models.Model):
    """
    Extended employee profile information.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
        ('O', 'Other'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('TERMINATED', 'Terminated'),
        ('ON_LEAVE', 'On Leave'),
        ('PROBATION', 'Probation'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Personal Information
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Employee's date of birth"
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        help_text="Gender identity"
    )
    marital_status = models.CharField(
        max_length=1,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        help_text="Marital status"
    )
    nationality = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nationality"
    )
    
    # Contact Information
    personal_email = models.EmailField(
        blank=True,
        help_text="Personal email address"
    )
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emergency contact person name"
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Emergency contact phone number"
    )
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text="Relationship with emergency contact"
    )
    
    # Address Information
    address_line_1 = models.CharField(
        max_length=200,
        blank=True,
        help_text="Address line 1"
    )
    address_line_2 = models.CharField(
        max_length=200,
        blank=True,
        help_text="Address line 2"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City"
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="State/Province"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Postal/ZIP code"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Country"
    )
    
    # Employment Information
    designation = models.CharField(max_length=128, blank=True)
    department = models.CharField(max_length=128, blank=True)
    dob = models.DateField(null=True, blank=True)
    doj = models.DateField(null=True, blank=True)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='ACTIVE',
        help_text="Current employment status"
    )
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='direct_reports')
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Salary and Benefits
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current salary (confidential)"
    )
    salary_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Salary currency code"
    )
    
    # Leave Balance Information
    annual_leaves = models.IntegerField(
        default=20,
        help_text="Annual leave balance (in days)"
    )
    sick_leaves = models.IntegerField(
        default=10,
        help_text="Sick leave balance (in days)"
    )
    maternity_leaves = models.IntegerField(
        default=90,
        help_text="Maternity leave balance (in days)"
    )
    paternity_leaves = models.IntegerField(
        default=15,
        help_text="Paternity leave balance (in days)"
    )
    emergency_leaves = models.IntegerField(
        default=5,
        help_text="Emergency leave balance (in days)"
    )
    compensatory_leaves = models.IntegerField(
        default=0,
        help_text="Compensatory leave balance (in days)"
    )
    
    # System fields
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the employee profile is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.designation or 'No Designation'}"
    
    @property
    def full_name(self):
        """Return the full name of the employee."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        """Calculate age from date of birth."""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def years_of_service(self):
        """Calculate years of service."""
        if self.date_of_joining:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_joining.year - (
                (today.month, today.day) < (self.date_of_joining.month, self.date_of_joining.day)
            )
        return None
    
    @property
    def full_address(self):
        """Return formatted full address."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    def can_be_managed_by(self, user):
        """Check if a user can manage this employee."""
        if user.is_superuser or user.is_admin_role():
            return True
        if user.is_hr():
            return True
        if user.is_manager() and self.manager == user:
            return True
        return False


class Attendance(models.Model):
    """
    Model to track employee attendance with login/logout times and device information.
    """
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    risk_score = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-date', '-login_time']
        unique_together = ['employee', 'date']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}"
    
    @property
    def working_hours(self):
        """Calculate total working hours for the day."""
        if self.login_time and self.logout_time:
            duration = self.logout_time - self.login_time
            return round(duration.total_seconds() / 3600, 2)
        return None
    
    @property
    def current_working_hours(self):
        """Calculate current working hours if still clocked in."""
        if self.login_time and not self.logout_time:
            from django.utils import timezone
            duration = timezone.now() - self.login_time
            return round(duration.total_seconds() / 3600, 2)
        return None
    
    @property
    def is_clocked_in(self):
        """Check if employee is currently clocked in."""
        return self.login_time is not None and self.logout_time is None
    
    @property
    def status(self):
        """Get current status of attendance."""
        if not self.login_time:
            return 'Not clocked in'
        elif not self.logout_time:
            return 'Clocked in'
        else:
            return 'Completed'


class Leave(models.Model):
    """
    Model to manage employee leave requests and approvals.
    """
    LEAVE_TYPE_CHOICES = [
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('COMPENSATORY', 'Compensatory Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        related_name='approvals', 
        on_delete=models.SET_NULL
    )
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-applied_on']
        verbose_name = 'Leave'
        verbose_name_plural = 'Leaves'
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type} ({self.from_date} to {self.to_date})"
    
    @property
    def duration_days(self):
        """Calculate the number of leave days."""
        return (self.to_date - self.from_date).days + 1


class Project(models.Model):
    """
    Model to represent projects within the organization.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
        ('CANCELLED', 'Cancelled'),
        ('PLANNING', 'Planning'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        """Return the number of project members."""
        return self.projectmember_set.count()


class ProjectMember(models.Model):
    """
    Model to represent project membership and roles.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=128, blank=True)
    joined_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project', 'employee']
        ordering = ['project__name', 'employee__first_name']
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
    
    def __str__(self):
        return f"{self.project.name} - {self.employee.get_full_name()} ({self.role or 'No Role'})"
