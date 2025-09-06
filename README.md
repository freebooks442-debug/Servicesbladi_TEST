# ServicesBladi - Local Development Setup

## Quick Start (One Command Setup)

```bash
cd backend
python setup_project.py
python manage.py runserver
```

## Manual Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- Virtual environment (recommended)

### 1. Database Setup (PostgreSQL)
```bash
# Start PostgreSQL service
sudo systemctl start postgresql

# Create database and user
sudo -iu postgres psql -c "CREATE USER servicesbladiuser WITH PASSWORD 'servicesbladi_pass';"
sudo -iu postgres psql -c "CREATE DATABASE servicesbladi OWNER servicesbladiuser;"
sudo -iu postgres psql -c "ALTER ROLE servicesbladiuser SET client_encoding TO 'utf8';"
sudo -iu postgres psql -c "ALTER ROLE servicesbladiuser SET default_transaction_isolation TO 'read committed';"
```

### 2. Python Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Django Setup
```bash
cd backend

# Run migrations
python manage.py migrate

# Load initial data (services, categories)
python manage.py load_initial_data

# Create superuser (optional - script creates default one)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

## Access Points

- **Main Website**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/django-admin/
- **Default Admin**: admin@servicesbladi.com / admin123

## Project Structure

```
ServicesBLADI/
├── backend/
│   ├── manage.py
│   ├── setup_project.py          # Automatic setup script
│   ├── requirements.txt           # Python dependencies
│   ├── servicesbladi/            # Main Django project
│   │   ├── settings.py           # Local settings (PostgreSQL)
│   │   └── urls.py
│   ├── accounts/                 # User management
│   ├── services/                 # Services management
│   ├── custom_requests/          # Request handling
│   ├── chatbot/                  # Chatbot functionality
│   ├── messaging/                # Messaging system
│   ├── resources/                # Resources management
│   └── notifications/            # Notifications
└── LOCAL_SETUP_SUMMARY.md       # Setup documentation
```

## Features

- ✅ User registration and authentication
- ✅ Service catalog with categories
- ✅ Service request management
- ✅ Admin panel for management
- ✅ Multi-language support (French, English, Arabic)
- ✅ Document upload and management
- ✅ Messaging system
- ✅ Notifications
- ✅ Chatbot integration (configurable)

## Configuration

### Database Settings
Located in `backend/servicesbladi/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'servicesbladi',
        'USER': 'servicesbladiuser',
        'PASSWORD': 'servicesbladi_pass',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

### Chatbot Configuration
To enable chatbot functionality, update these settings:
```python
AZURE_OPENAI_ENDPOINT = "your-openai-endpoint"
AZURE_OPENAI_API_KEY = "your-api-key"
```

## Production Deployment

For production deployment:

1. Update `DEBUG = False` in settings
2. Set a secure `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Use environment variables for sensitive data
5. Set up proper media/static file serving
6. Configure HTTPS and security headers

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running: `sudo systemctl status postgresql`
   - Check database credentials in settings.py

2. **"No active services found"**
   - Run: `python manage.py load_initial_data`

3. **Static Files Not Loading**
   - Run: `python manage.py collectstatic`

4. **Permission Errors**
   - Ensure proper file permissions
   - Check virtual environment activation

### Reset Database
```bash
# Drop and recreate database
sudo -iu postgres psql -c "DROP DATABASE servicesbladi;"
sudo -iu postgres psql -c "CREATE DATABASE servicesbladi OWNER servicesbladiuser;"

# Re-run setup
cd backend
python setup_project.py
```

## Support

For issues or questions, check the troubleshooting section above or review the logs in the Django development server output.
