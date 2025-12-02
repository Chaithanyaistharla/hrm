from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with default password and role assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the superuser (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@hrms.com',
            help='Email for the superuser (default: admin@hrms.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the superuser (default: admin123)',
        )
        parser.add_argument(
            '--role',
            type=str,
            default='ADMIN',
            help='Role to assign to the superuser (default: ADMIN)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        role_name = options['role']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with username "{username}" already exists.')
            )
            user = User.objects.get(username=username)
        else:
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully.')
            )

        # Assign role
        try:
            role = Role.objects.get(name=role_name)
            user.role = role
            user.employee_id = 'ADMIN001'
            user.department = 'IT Administration'
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Assigned role "{role.get_name_display()}" to user "{username}".')
            )
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Role "{role_name}" not found. Available roles: {", ".join([r.name for r in Role.objects.all()])}')
            )

        # Display login credentials
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SUPERUSER LOGIN CREDENTIALS:'))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Role: {user.role.get_name_display() if user.role else "No Role"}')
        self.stdout.write('='*50)