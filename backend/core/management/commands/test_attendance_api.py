from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test attendance clock-in/out API endpoints'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Attendance API Endpoints'))
        
        # Create a test user if doesn't exist
        username = 'test_employee'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='test@example.com',
                password='testpass123',
                role='EMPLOYEE',
                first_name='Test',
                last_name='Employee'
            )
            self.stdout.write(f'Created test user: {username}')
        
        # Create a test client and login
        client = Client()
        client.login(username=username, password='testpass123')
        
        self.stdout.write('\\n1. Testing Clock-In API:')
        clock_in_url = reverse('attendance_clock_in')
        response = client.post(clock_in_url, content_type='application/json')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS(f'✓ Clock-in successful: {data["message"]}'))
            self.stdout.write(f'  Data: {json.dumps(data["data"], indent=2)}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Clock-in failed: {response.content}'))
        
        self.stdout.write('\\n2. Testing Attendance Status API:')
        status_url = reverse('attendance_status')
        response = client.get(status_url)
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS(f'✓ Status retrieved: {data["message"]}'))
            self.stdout.write(f'  Data: {json.dumps(data["data"], indent=2)}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Status failed: {response.content}'))
        
        self.stdout.write('\\n3. Testing Clock-Out API:')
        clock_out_url = reverse('attendance_clock_out')
        response = client.post(clock_out_url, content_type='application/json')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS(f'✓ Clock-out successful: {data["message"]}'))
            self.stdout.write(f'  Data: {json.dumps(data["data"], indent=2)}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Clock-out failed: {response.content}'))
        
        self.stdout.write('\\n4. Testing Final Status:')
        response = client.get(status_url)
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS(f'✓ Final status: {data["message"]}'))
            self.stdout.write(f'  Working hours: {data["data"].get("working_hours", "N/A")}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Final status failed: {response.content}'))
        
        self.stdout.write('\\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Attendance API Testing Complete!'))