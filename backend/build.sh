#!/usr/bin/env bash
# Render.com build script for ServicesBladi

set -o errexit  # exit on error

echo "🚀 Starting Render deployment for ServicesBladi..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist (safely)
echo "👤 Setting up admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(name='admin').exists():
    User.objects.create_superuser('admin', 'admin@servicesbladi.com', 'admin123')
    print('✅ Admin user created: admin/admin123')
else:
    print('✅ Admin user already exists')
"

# Load initial data (optional, won't fail if missing)
echo "📊 Loading initial data..."
python manage.py load_initial_data || echo "⚠️ Initial data command not found (this is normal)"

# Initialize chatbot config (optional)
echo "🤖 Initializing chatbot..."
python manage.py init_chatbot_config || echo "ℹ️ Chatbot config skipped (Azure OpenAI not configured)"

echo "✅ Build completed successfully!"
echo "🌐 ServicesBladi is ready to serve!"
