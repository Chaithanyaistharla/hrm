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
