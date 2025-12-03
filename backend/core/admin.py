from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile, Attendance, Leave, Project, ProjectMember


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


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'login_time', 'logout_time', 'location', 'risk_score']
    list_filter = ['date', 'employee__role', 'location', 'risk_score']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'location', 'ip']
    date_hierarchy = 'date'
    readonly_fields = ['risk_score']
    
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date')
        }),
        ('Time Tracking', {
            'fields': ('login_time', 'logout_time')
        }),
        ('Location & Device Info', {
            'fields': ('ip', 'device_info', 'location', 'risk_score')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee')


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'from_date', 'to_date', 'status', 'approver', 'applied_on']
    list_filter = ['leave_type', 'status', 'from_date', 'to_date', 'applied_on']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
    date_hierarchy = 'from_date'
    readonly_fields = ['applied_on', 'approved_on']
    
    fieldsets = (
        ('Leave Request', {
            'fields': ('employee', 'leave_type', 'from_date', 'to_date', 'reason')
        }),
        ('Approval', {
            'fields': ('status', 'approver', 'applied_on', 'approved_on')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'approver')
    
    def save_model(self, request, obj, form, change):
        if obj.status in ['APPROVED', 'REJECTED'] and not obj.approved_on:
            from django.utils import timezone
            obj.approved_on = timezone.now()
            if not obj.approver:
                obj.approver = request.user
        super().save_model(request, obj, form, change)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'status', 'start_date', 'end_date', 'member_count', 'created_at']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['name', 'description', 'manager__username', 'manager__first_name', 'manager__last_name']
    date_hierarchy = 'start_date'
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('name', 'description', 'manager', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Metadata', {
            'fields': ('member_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('manager')


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'employee', 'role', 'joined_on']
    list_filter = ['role', 'joined_on', 'project__status']
    search_fields = ['project__name', 'employee__username', 'employee__first_name', 'employee__last_name', 'role']
    readonly_fields = ['joined_on']
    
    fieldsets = (
        ('Project Assignment', {
            'fields': ('project', 'employee', 'role', 'joined_on')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'employee')
    

