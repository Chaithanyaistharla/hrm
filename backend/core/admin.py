from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile


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
    list_display = ['user', 'designation', 'employment_status', 'date_of_joining', 'manager']
    list_filter = ['employment_status', 'date_of_joining', 'manager']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'designation']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'designation', 'employment_status', 'manager')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'marital_status', 'nationality')
        }),
        ('Contact Information', {
            'fields': ('personal_email', 'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone')
        }),
        ('Address Information', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Employment Details', {
            'fields': ('date_of_joining', 'work_location', 'salary', 'salary_currency')
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
            readonly_fields.extend(['salary', 'salary_currency'])
        return readonly_fields
