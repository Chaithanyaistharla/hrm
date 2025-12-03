from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta, datetime, time
from core.models import User, Leave, Attendance, TimesheetEntry, Project, ProjectMember
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for dashboard testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data for dashboard testing...")
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='john_doe',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@company.com',
                'role': 'EMPLOYEE',
                'department': 'Engineering'
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f"Created user: {user.username}")
        
        # Create sample project
        project, created = Project.objects.get_or_create(
            name='Dashboard Demo Project',
            defaults={
                'description': 'A sample project for dashboard demonstration',
                'manager': user,
                'status': 'ACTIVE'
            }
        )
        if created:
            self.stdout.write(f"Created project: {project.name}")
        
        # Add user to project
        member, created = ProjectMember.objects.get_or_create(
            project=project,
            employee=user,
            defaults={'role': 'Developer'}
        )
        
        # Create sample attendance records for this week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        for i in range(5):  # Monday to Friday
            work_date = week_start + timedelta(days=i)
            if work_date <= today:
                attendance, created = Attendance.objects.get_or_create(
                    employee=user,
                    date=work_date,
                    defaults={
                        'login_time': timezone.make_aware(datetime.combine(work_date, time(9, random.randint(0, 30)))),
                        'logout_time': timezone.make_aware(datetime.combine(work_date, time(17, random.randint(30, 59))))
                    }
                )
                if created:
                    self.stdout.write(f"Created attendance for {work_date}")
        
        # Create sample timesheet entries
        for i in range(5):
            work_date = week_start + timedelta(days=i)
            if work_date <= today:
                try:
                    entry, created = TimesheetEntry.objects.get_or_create(
                        employee=user,
                        date=work_date,
                        project=project,
                        defaults={
                            'hours': round(7.5 + random.uniform(-0.5, 1), 1),
                            'description': f'Development work on {project.name}'
                        }
                    )
                    if created:
                        self.stdout.write(f"Created timesheet entry for {work_date}: {entry.hours}h")
                except Exception as e:
                    # Handle duplicate entries
                    self.stdout.write(f"Timesheet entry already exists for {work_date}")
        
        # Create sample leave requests
        future_date = today + timedelta(days=10)
        leave, created = Leave.objects.get_or_create(
            employee=user,
            from_date=future_date,
            to_date=future_date + timedelta(days=1),
            defaults={
                'leave_type': 'ANNUAL',
                'reason': 'Vacation',
                'status': 'PENDING'
            }
        )
        if created:
            self.stdout.write(f"Created leave request: {leave}")
        
        self.stdout.write(self.style.SUCCESS("Sample data created successfully!"))
        self.stdout.write(f"Test user credentials: username=john_doe, password=password123")