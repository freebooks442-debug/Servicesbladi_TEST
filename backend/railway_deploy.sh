#!/bin/bash

# Railway deployment script
echo "🚀 Starting Railway deployment..."

# Set Python path and Django settings
export PYTHONPATH=/app:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=servicesbladi.settings

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
python manage.py shell << EOF
from accounts.models import Utilisateur
if not Utilisateur.objects.filter(name='admin').exists():
    user = Utilisateur.objects.create_superuser(
        name='admin',
        email='admin@servicesbladi.com', 
        password='admin123'
    )
    print("✅ Superuser created")
else:
    print("✅ Superuser already exists")
EOF

# Load initial data
echo "📊 Loading initial data..."
python manage.py load_initial_data

echo "✅ Deployment setup complete!"
