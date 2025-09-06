#!/bin/bash

# Railway deployment script
echo "🚀 Starting Railway deployment..."

# Set environment variables
export PYTHONPATH=/app:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=servicesbladi.settings

# Function to check if command succeeded
check_command() {
    if [ $? -ne 0 ]; then
        echo "❌ Error: $1 failed"
        exit 1
    else
        echo "✅ $1 completed successfully"
    fi
}

# Install any missing dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
check_command "Dependency installation"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput
check_command "Static files collection"

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput
check_command "Database migration"

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
python manage.py shell << 'EOF'
try:
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
except Exception as e:
    print(f"⚠️ Error creating superuser: {e}")
    print("ℹ️ You can create one manually later")
EOF

# Load initial data (optional, may fail on first run)
echo "📊 Loading initial data..."
python manage.py load_initial_data || echo "⚠️ Initial data loading failed (this is normal on first deployment)"

# Initialize chatbot configuration (optional)
echo "🤖 Initializing chatbot configuration..."
python manage.py init_chatbot_config || echo "⚠️ Chatbot initialization failed (this is normal if Azure OpenAI is not configured)"

echo "✅ Deployment setup complete!"
echo "🌐 Your application should be ready to serve traffic"
