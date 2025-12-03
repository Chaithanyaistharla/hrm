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
    list_display = ['user', 'designation', 'department', 'doj', 'manager']
    list_filter = ['department', 'doj', 'manager']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'designation', 'department']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'designation', 'department', 'manager', 'phone', 'location')
        }),
        ('Important Dates', {
            'fields': ('dob', 'doj')
        }),
    )
    

