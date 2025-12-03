from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from .models import Role


def role_required(*roles):
    """
    Decorator to require specific role(s) for function-based views.
    Usage: @role_required('HR', 'ADMIN')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                messages.error(request, f'Access denied. Required role: {", ".join(roles)}')
                return HttpResponseForbidden("You don't have permission to access this resource.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin(AccessMixin):
    """
    Mixin for class-based views that require specific role(s).
    Usage: class MyView(RoleRequiredMixin, ListView):
               required_roles = ['HR', 'ADMIN']
    """
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not hasattr(request.user, 'role') or request.user.role not in self.required_roles:
            messages.error(request, f'Access denied. Required role: {", ".join(self.required_roles)}')
            return HttpResponseForbidden("You don't have permission to access this resource.")
        
        return super().dispatch(request, *args, **kwargs)


# Convenience decorators for specific roles
admin_required = role_required(Role.ADMIN)
hr_required = role_required(Role.HR, Role.ADMIN)
manager_required = role_required(Role.MANAGER, Role.HR, Role.ADMIN)


def manager_or_hr_required(view_func):
    """
    Decorator to require manager, HR, or admin role for leave approval functionality.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_hr() or user.is_manager() or user.is_admin_role():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. You must be a Manager, HR, or Admin to access this resource.')
        return HttpResponseForbidden("You don't have permission to access this resource.")
    return wrapper


def can_manage_leave(user, leave):
    """
    Check if a user can manage (approve/reject) a specific leave.
    """
    # HR and Admin can manage all leaves
    if user.is_hr() or user.is_admin_role():
        return True
    
    # Managers can only manage their direct reports' leaves
    if user.is_manager():
        try:
            employee_profile = leave.employee.employeeprofile
            return employee_profile.manager == user
        except:
            return False
    
    return False


class AdminRequiredMixin(RoleRequiredMixin):
    required_roles = [Role.ADMIN]


class HRRequiredMixin(RoleRequiredMixin):
    required_roles = [Role.HR, Role.ADMIN]


class ManagerRequiredMixin(RoleRequiredMixin):
    required_roles = [Role.MANAGER, Role.HR, Role.ADMIN]