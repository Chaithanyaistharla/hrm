# Backend - HRMS Core (Django API)

Django backend API for the HRMS system.

## Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
backend/
├── hrms_core/          # Django project settings
│   ├── __init__.py
│   ├── settings.py     # Main settings
│   ├── urls.py         # URL routing
│   ├── wsgi.py         # WSGI config
│   └── asgi.py         # ASGI config
├── core/               # Main Django app
│   ├── models.py       # Database models
│   ├── views.py        # API views
│   ├── serializers.py  # DRF serializers (to be added)
│   ├── urls.py         # App URLs (to be added)
│   └── migrations/     # Database migrations
├── requirements.txt    # Python dependencies
└── manage.py          # Django management
```

## API Development

For API development, consider adding:

1. **Django REST Framework:**
   ```bash
   pip install djangorestframework
   pip install djangorestframework-simplejwt  # For JWT authentication
   ```

2. **CORS Headers:**
   ```bash
   pip install django-cors-headers
   ```

## Environment Variables

The backend uses environment variables from the root `.env` file:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- Database configuration

## Future Additions

As the system grows, you can add specialized Django apps:
- `employees/` - Employee management
- `attendance/` - Attendance tracking
- `payroll/` - Payroll management
- `leave/` - Leave management