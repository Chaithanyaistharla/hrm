from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Create default roles for the HRMS system'

    def handle(self, *args, **options):
        """Create default roles with descriptions."""
        
        roles_data = [
            {
                'name': 'EMPLOYEE',
                'description': 'Regular employee with basic access to personal information and company resources.',
            },
            {
                'name': 'MANAGER',
                'description': 'Team manager with access to team member information and reporting capabilities.',
            },
            {
                'name': 'HR',
                'description': 'Human Resources personnel with access to all employee information and HR processes.',
            },
            {
                'name': 'ADMIN',
                'description': 'System administrator with full access to all system features and configurations.',
            },
        ]

        created_count = 0
        updated_count = 0

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.get_name_display()}')
                )
            else:
                # Update description if it's different
                if role.description != role_data['description']:
                    role.description = role_data['description']
                    role.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated role: {role.get_name_display()}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Role already exists: {role.get_name_display()}')
                    )

        # Summary
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully created {created_count} new roles.')
            )
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Updated {updated_count} existing roles.')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal roles in system: {Role.objects.count()}')
        )