from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import EmployeeProfile, Leave, Role
from django.utils import timezone
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for leave approval system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data for leave approval system...'))
        
        # Create HR user
        hr_user, created = User.objects.get_or_create(
            username='hr_user',
            defaults={
                'first_name': 'HR',
                'last_name': 'Manager',
                'email': 'hr@company.com',
                'role': Role.HR,
                'employee_id': 'HR001',
                'department': 'Human Resources'
            }
        )
        if created:
            hr_user.set_password('password123')
            hr_user.save()
            self.stdout.write(f'Created HR user: {hr_user.username}')
        
        # Create or update employee profile
        hr_profile, created = EmployeeProfile.objects.get_or_create(
            user=hr_user,
            defaults={
                'designation': 'HR Manager',
                'department': 'Human Resources'
            }
        )
        if created:
            self.stdout.write(f'Created HR profile for: {hr_user.username}')

        # Create Manager user
        manager_user, created = User.objects.get_or_create(
            username='manager_user',
            defaults={
                'first_name': 'John',
                'last_name': 'Manager',
                'email': 'john.manager@company.com',
                'role': Role.MANAGER,
                'employee_id': 'MGR001',
                'department': 'Engineering'
            }
        )
        if created:
            manager_user.set_password('password123')
            manager_user.save()
            self.stdout.write(f'Created Manager user: {manager_user.username}')
        
        # Create or update employee profile
        manager_profile, created = EmployeeProfile.objects.get_or_create(
            user=manager_user,
            defaults={
                'designation': 'Engineering Manager',
                'department': 'Engineering'
            }
        )
        if created:
            self.stdout.write(f'Created Manager profile for: {manager_user.username}')

        # Create Employee users (direct reports to manager)
        employees = []
        for i in range(1, 4):  # Create 3 employees
            emp_user, created = User.objects.get_or_create(
                username=f'employee{i}',
                defaults={
                    'first_name': f'Employee',
                    'last_name': f'User{i}',
                    'email': f'employee{i}@company.com',
                    'role': Role.EMPLOYEE,
                    'employee_id': f'EMP00{i}',
                    'department': 'Engineering'
                }
            )
            if created:
                emp_user.set_password('password123')
                emp_user.save()
                self.stdout.write(f'Created Employee user: {emp_user.username}')
            
            # Create or update employee profile
            emp_profile, created = EmployeeProfile.objects.get_or_create(
                user=emp_user,
                defaults={
                    'designation': f'Software Developer {i}',
                    'department': 'Engineering',
                    'manager': manager_user  # Set manager as the direct manager
                }
            )
            if created:
                self.stdout.write(f'Created Employee profile for: {emp_user.username}')
            else:
                # Update manager if not set
                if not emp_profile.manager:
                    emp_profile.manager = manager_user
                    emp_profile.save()
                    self.stdout.write(f'Updated manager for: {emp_user.username}')
                    
            employees.append(emp_user)

        # Create some leave applications
        leave_types = ['ANNUAL', 'SICK', 'EMERGENCY', 'COMPENSATORY']
        
        for i, employee in enumerate(employees):
            # Create 2-3 leaves per employee
            for j in range(random.randint(2, 3)):
                start_date = date.today() + timedelta(days=random.randint(1, 30))
                duration = random.randint(1, 5)
                end_date = start_date + timedelta(days=duration - 1)
                
                leave_type = random.choice(leave_types)
                
                # Make some leaves pending, some approved, some rejected
                if j == 0:
                    status = 'PENDING'
                    approver = None
                    approved_on = None
                elif j == 1:
                    status = 'APPROVED'
                    approver = manager_user if random.choice([True, False]) else hr_user
                    approved_on = timezone.now() - timedelta(days=random.randint(1, 10))
                else:
                    status = 'REJECTED'
                    approver = manager_user if random.choice([True, False]) else hr_user
                    approved_on = timezone.now() - timedelta(days=random.randint(1, 10))
                
                leave = Leave.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    from_date=start_date,
                    to_date=end_date,
                    reason=f'Test {leave_type.lower()} leave request for {employee.get_full_name()}',
                    status=status,
                    approver=approver,
                    approved_on=approved_on,
                    rejection_reason='Test rejection reason' if status == 'REJECTED' else ''
                )
                self.stdout.write(f'Created {status} leave for {employee.username}: {leave_type} ({start_date} to {end_date})')

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write('')
        self.stdout.write('Test Login Credentials:')
        self.stdout.write('HR User: username=hr_user, password=password123')
        self.stdout.write('Manager User: username=manager_user, password=password123') 
        self.stdout.write('Employee Users: username=employee1/employee2/employee3, password=password123')