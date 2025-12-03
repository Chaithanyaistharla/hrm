from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import re


class RoleRequiredMiddleware:
    def __init__(self, get_response): 
        self.get_response = get_response
    
    def __call__(self, request):
        # skip anon and admin pages
        # Add per-path rules or decorator-based checks later
        return self.get_response(request)


class RoleBasedAccessMiddleware:
    """
    Middleware to handle role-based access control.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define role-based access rules
        self.role_permissions = {
            'ADMIN': [
                r'^/admin/',
                r'^/dashboard/',
                r'^/profile/',
                r'^/users/',
                r'^/reports/',
                r'^/hr/',
                r'^/management/',
            ],
            'HR': [
                r'^/dashboard/',
                r'^/profile/',
                r'^/employees/',
                r'^/reports/',
                r'^/hr/',
            ],
            'MANAGER': [
                r'^/dashboard/',
                r'^/profile/',
                r'^/team/',
                r'^/reports/team/',
            ],
            'EMPLOYEE': [
                r'^/dashboard/',
                r'^/profile/',
                r'^/attendance/my/',
                r'^/leave/my/',
            ],
        }
        
        # Paths that don't require authentication
        self.public_paths = [
            r'^/login/$',
            r'^/logout/$',
            r'^/static/',
            r'^/media/',
            r'^/$',  # root path
        ]
        
        # Paths that require authentication but no specific role
        self.authenticated_paths = [
            r'^/dashboard/$',
            r'^/profile/$',
        ]

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view to check role-based permissions.
        """
        path = request.path
        user = request.user
        
        # Check if path is public (no authentication required)
        if self.is_public_path(path):
            return None
        
        # Check if user is authenticated
        if not user.is_authenticated:
            if not path.startswith('/login'):
                return redirect(f"{reverse('login')}?next={path}")
            return None
        
        # Check if path requires authentication only
        if self.is_authenticated_path(path):
            return None
        
        # Check role-based permissions
        if user.role and self.has_permission(user.role.name, path):
            return None
        
        # Superuser has access to everything
        if user.is_superuser:
            return None
        
        # Access denied
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')

    def is_public_path(self, path):
        """Check if the path is public (no authentication required)."""
        for pattern in self.public_paths:
            if re.match(pattern, path):
                return True
        return False

    def is_authenticated_path(self, path):
        """Check if the path requires authentication but no specific role."""
        for pattern in self.authenticated_paths:
            if re.match(pattern, path):
                return True
        return False

    def has_permission(self, role_name, path):
        """Check if a role has permission to access a specific path."""
        if role_name not in self.role_permissions:
            return False
        
        allowed_patterns = self.role_permissions[role_name]
        for pattern in allowed_patterns:
            if re.match(pattern, path):
                return True
        
        return False


def role_required(required_roles):
    """
    Decorator to require specific roles for view access.
    
    Usage:
    @role_required(['HR', 'ADMIN'])
    def some_view(request):
        pass
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not request.user.role:
                messages.error(request, 'No role assigned. Please contact administrator.')
                return redirect('dashboard')
            
            if request.user.role.name not in required_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(view_func):
    """Decorator to require ADMIN role."""
    return role_required(['ADMIN'])(view_func)


def hr_or_admin_required(view_func):
    """Decorator to require HR or ADMIN role."""
    return role_required(['HR', 'ADMIN'])(view_func)


def manager_or_above_required(view_func):
    """Decorator to require MANAGER, HR, or ADMIN role."""
    return role_required(['MANAGER', 'HR', 'ADMIN'])(view_func)