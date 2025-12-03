from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Project, ProjectMember, Role
from django.utils import timezone
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for project management system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data for project management system...'))
        
        # Get existing users
        try:
            hr_user = User.objects.get(username='hr_user')
            manager_user = User.objects.get(username='manager_user')
            employees = User.objects.filter(username__in=['employee1', 'employee2', 'employee3'])
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Test users not found. Please run create_leave_test_data first.'))
            return

        # Create sample projects
        projects_data = [
            {
                'name': 'Employee Portal Redesign',
                'description': 'Redesign the internal employee portal with modern UI/UX and improved functionality',
                'manager': manager_user,
                'status': 'ACTIVE',
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=60),
            },
            {
                'name': 'Mobile App Development',
                'description': 'Develop a mobile application for employee self-service and HR management',
                'manager': hr_user,
                'status': 'PLANNING',
                'start_date': date.today() + timedelta(days=15),
                'end_date': date.today() + timedelta(days=120),
            },
            {
                'name': 'Data Migration Project',
                'description': 'Migrate legacy HR data to the new system with data validation and cleanup',
                'manager': manager_user,
                'status': 'ACTIVE',
                'start_date': date.today() - timedelta(days=15),
                'end_date': date.today() + timedelta(days=45),
            },
            {
                'name': 'Performance Management System',
                'description': 'Implement a comprehensive performance review and goal tracking system',
                'manager': hr_user,
                'status': 'ON_HOLD',
                'start_date': date.today() - timedelta(days=45),
                'end_date': None,
            },
            {
                'name': 'Training Portal',
                'description': 'Create an online training platform for employee skill development',
                'manager': manager_user,
                'status': 'COMPLETED',
                'start_date': date.today() - timedelta(days=90),
                'end_date': date.today() - timedelta(days=10),
            }
        ]

        created_projects = []
        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                name=project_data['name'],
                defaults=project_data
            )
            if created:
                created_projects.append(project)
                self.stdout.write(f'Created project: {project.name}')
            else:
                self.stdout.write(f'Project already exists: {project.name}')

        # Assign team members to projects
        roles = ['Developer', 'Senior Developer', 'UI/UX Designer', 'QA Tester', 'Business Analyst', 'Technical Lead']
        
        for project in created_projects:
            # Assign 2-3 employees per project
            available_employees = list(employees)
            random.shuffle(available_employees)
            members_to_add = available_employees[:random.randint(2, 3)]
            
            for employee in members_to_add:
                # Check if already a member
                if not ProjectMember.objects.filter(project=project, employee=employee).exists():
                    role = random.choice(roles)
                    ProjectMember.objects.create(
                        project=project,
                        employee=employee,
                        role=role
                    )
                    self.stdout.write(f'Added {employee.get_full_name()} to "{project.name}" as {role}')

        # Add manager as project member for some projects
        for project in created_projects[:2]:  # First 2 projects
            if not ProjectMember.objects.filter(project=project, employee=project.manager).exists():
                ProjectMember.objects.create(
                    project=project,
                    employee=project.manager,
                    role='Technical Lead'
                )
                self.stdout.write(f'Added project manager {project.manager.get_full_name()} to "{project.name}" as Technical Lead')

        self.stdout.write(self.style.SUCCESS('Project test data created successfully!'))
        self.stdout.write('')
        self.stdout.write('You can now:')
        self.stdout.write('1. Login as HR (hr_user) to manage all projects')
        self.stdout.write('2. Login as Manager (manager_user) to see managed projects')
        self.stdout.write('3. Login as Employee (employee1/2/3) to view assigned projects')