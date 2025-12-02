# HRMS Core - Human Resource Management System

A full-stack Human Resource Management System with Django backend and modern frontend for managing employees, attendance, and other HR operations.

## Project Structure

```
hrms/
├── backend/            # Django API backend
│   ├── hrms_core/     # Django project settings
│   ├── core/          # Main Django app
│   ├── requirements.txt
│   └── manage.py
├── frontend/          # Frontend application
│   └── README.md      # Frontend setup instructions
├── database/          # Database files and configurations
│   └── README.md      # Database documentation
├── venv/             # Python virtual environment
├── .env              # Environment variables
├── .gitignore        # Git ignore rules
└── README.md         # This file
```

## Quick Start

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   # Follow instructions in frontend/README.md
   # Choose your preferred frontend framework
   ```

## Environment Configuration

Key environment variables in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DATABASE_*` - Database configuration

## Development Workflow

### Backend Development
- Navigate to `backend/` directory
- Django API development
- Database models and migrations
- REST API endpoints

### Frontend Development
- Navigate to `frontend/` directory
- UI/UX development
- API integration
- User interface components

### Database Management
- Database files stored in `database/` directory
- Migrations managed from backend
- Backup and restore procedures in `database/README.md`

## Future Extensions

The system can be extended with specialized modules:
- Employee management
- Attendance tracking  
- Payroll management
- Leave management
- Performance reviews
- Recruitment management