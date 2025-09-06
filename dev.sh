#!/bin/bash
# ServicesBladi Quick Start Script
# This script activates the virtual environment and provides easy commands

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "🚀 ServicesBladi Development Environment"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at $VENV_DIR"
    echo "Please create one with: python -m venv .venv"
    exit 1
fi

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "📦 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "✅ Virtual environment already active"
fi

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r "$BACKEND_DIR/requirements.txt"
fi

# Change to backend directory
cd "$BACKEND_DIR"

echo ""
echo "📋 Available commands:"
echo "  setup    - Run initial setup (migrations, data, etc.)"
echo "  run      - Start development server"
echo "  admin    - Create superuser"
echo "  shell    - Open Django shell"
echo "  migrate  - Run migrations"
echo "  test     - Run tests"
echo ""

# Function to run setup
run_setup() {
    echo "🔧 Running setup..."
    python setup_project.py
}

# Function to run server
run_server() {
    echo "🌐 Starting development server..."
    python manage.py runserver
}

# Function to create admin
create_admin() {
    echo "👤 Creating superuser..."
    python manage.py createsuperuser
}

# Function to open shell
open_shell() {
    echo "🐍 Opening Django shell..."
    python manage.py shell
}

# Function to run migrations
run_migrations() {
    echo "📊 Running migrations..."
    python manage.py migrate
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    python manage.py test
}

# Handle command line arguments
case "${1:-run}" in
    "setup")
        run_setup
        ;;
    "run")
        run_server
        ;;
    "admin")
        create_admin
        ;;
    "shell")
        open_shell
        ;;
    "migrate")
        run_migrations
        ;;
    "test")
        run_tests
        ;;
    *)
        echo "Usage: $0 {setup|run|admin|shell|migrate|test}"
        echo "Default: run"
        echo ""
        echo "Starting development server by default..."
        run_server
        ;;
esac
