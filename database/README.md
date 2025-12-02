# Database - HRMS Core

This folder contains database-related files and configurations.

## Current Setup

- **Database Engine**: SQLite (for development)
- **Database File**: `db.sqlite3` (when created)

## Production Options

For production, consider these database options:

### PostgreSQL (Recommended)
- Robust and scalable
- Good for complex queries
- ACID compliance

### MySQL/MariaDB
- Popular choice
- Good performance
- Wide hosting support

### Database Configuration

Update the backend Django settings for production databases:

```python
# In backend/hrms_core/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST', default='localhost'),
        'PORT': config('DATABASE_PORT', default='5432'),
    }
}
```

## Database Migrations

Run migrations from the backend directory:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## Backup and Restore

For SQLite:
```bash
# Backup
cp database/db.sqlite3 database/backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Restore
cp database/backup_YYYYMMDD_HHMMSS.sqlite3 database/db.sqlite3
```