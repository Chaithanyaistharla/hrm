from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, EmployeeProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['name', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Fields to display in the admin list view
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'is_staff']
    list_filter = ['role', 'department', 'is_active', 'is_staff', 'is_superuser', 'hire_date']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id']
    
    # Add custom fields to the user edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'hire_date')
        }),
    )
    
    # Add custom fields to the user creation form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'hire_date')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'designation', 'department', 'employee_type', 'status', 'date_of_joining', 'manager']
    list_filter = ['department', 'employee_type', 'status', 'date_of_joining', 'manager']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'designation', 'department']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'designation', 'department', 'employee_type', 'status', 'manager')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'marital_status', 'nationality')
        }),
        ('Contact Information', {
            'fields': ('personal_email', 'personal_phone', 'alternate_phone')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone')
        }),
        ('Address Information', {
            'fields': ('current_address', 'permanent_address')
        }),
        ('Employment Details', {
            'fields': ('date_of_joining', 'probation_end_date', 'notice_period_days', 'salary')
        }),
        ('Bank Details', {
            'fields': ('bank_account_number', 'bank_name', 'bank_branch', 'ifsc_code')
        }),
        ('Identity Documents', {
            'fields': ('pan_number', 'aadhar_number', 'passport_number')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # Inline editing support
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.extend(['salary', 'bank_account_number', 'bank_name', 'bank_branch', 'ifsc_code'])
        return readonly_fields
