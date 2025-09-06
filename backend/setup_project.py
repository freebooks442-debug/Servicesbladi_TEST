#!/usr/bin/env python
"""
Automatic setup script for ServicesBladi project
This script ensures the database is properly configured and populated
"""
import os
import sys
import django
from pathlib import Path


def setup_django():
    """Configure Django settings"""
    # Add the backend directory to Python path
    backend_dir = Path(__file__).parent
    sys.path.insert(0, str(backend_dir))
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicesbladi.settings')
    
    # Setup Django
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"Error setting up Django: {e}")
        return False


def check_database():
    """Check if database is accessible"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


def run_migrations():
    """Run database migrations"""
    try:
        from django.core.management import execute_from_command_line
        print("Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=0'])
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False


def load_initial_data():
    """Load initial services data if needed"""
    try:
        from services.models import Service
        from django.core.management import execute_from_command_line
        
        # Check if services exist
        if Service.objects.count() == 0:
            print("Loading initial services data...")
            execute_from_command_line(['manage.py', 'load_initial_data'])
            print("✅ Initial data loaded successfully")
        else:
            print(f"✅ Database already contains {Service.objects.count()} services")
        return True
    except Exception as e:
        print(f"❌ Error loading initial data: {e}")
        return False


def create_superuser_if_needed():
    """Create a default superuser if none exists"""
    try:
        from accounts.models import Utilisateur
        
        # Check if any superuser exists
        if not Utilisateur.objects.filter(is_superuser=True).exists():
            print("Creating default superuser...")
            user = Utilisateur.objects.create_user(
                email='admin@servicesbladi.com',
                password='admin123'
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print("✅ Default superuser created: admin@servicesbladi.com / admin123")
        else:
            print("✅ Superuser already exists")
        return True
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False


def collect_static_files():
    """Collect static files for production"""
    try:
        from django.core.management import execute_from_command_line
        print("Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--verbosity=0'])
        print("✅ Static files collected successfully")
        return True
    except Exception as e:
        print(f"❌ Error collecting static files: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Starting ServicesBladi Setup...")
    print("=" * 50)
    
    # Setup Django
    if not setup_django():
        sys.exit(1)
    
    # Check database connection
    print("Checking database connection...")
    if not check_database():
        print("❌ Cannot connect to database. Please ensure PostgreSQL is running.")
        sys.exit(1)
    print("✅ Database connection successful")
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Load initial data
    if not load_initial_data():
        sys.exit(1)
    
    # Create superuser if needed
    if not create_superuser_if_needed():
        sys.exit(1)
    
    # Collect static files
    if not collect_static_files():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 ServicesBladi setup completed successfully!")
    print("\n📋 Quick Start:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Visit: http://127.0.0.1:8000/")
    print("3. Admin panel: http://127.0.0.1:8000/django-admin/")
    print("4. Admin credentials: admin@servicesbladi.com / admin123")
    print("\n✅ The project is ready to use!")


if __name__ == '__main__':
    main()
