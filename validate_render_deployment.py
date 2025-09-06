#!/usr/bin/env python3
"""
Render.com Deployment Validation Script for ServicesBladi
Run this before deploying to ensure everything is ready
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def check_file_executable(file_path, description):
    """Check if a file is executable"""
    if os.path.exists(file_path) and os.access(file_path, os.X_OK):
        print(f"✅ {description}: {file_path} - EXECUTABLE")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT EXECUTABLE")
        return False

def main():
    print("🔍 Validating ServicesBladi for Render.com deployment...\n")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    os.chdir(backend_dir)
    
    all_good = True
    
    print("📁 Checking essential files:")
    files_to_check = [
        ("requirements.txt", "Python dependencies"),
        ("manage.py", "Django management script"),
        ("build.sh", "Render build script"),
        ("render.env.example", "Environment variables template"),
        ("servicesbladi/settings.py", "Django settings"),
        ("servicesbladi/wsgi.py", "WSGI application"),
        ("servicesbladi/asgi.py", "ASGI application"),
        ("servicesbladi/urls.py", "URL configuration")
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print(f"\n🔧 Checking executable permissions:")
    executables = [
        ("build.sh", "Build script"),
    ]
    
    for file_path, description in executables:
        if not check_file_executable(file_path, description):
            all_good = False
    
    print(f"\n📦 Checking key dependencies in requirements.txt:")
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
            
        required_packages = [
            "Django", "gunicorn", "psycopg2-binary", "whitenoise", 
            "dj-database-url", "django-cors-headers", "channels"
        ]
        
        for package in required_packages:
            if package.lower() in requirements.lower():
                print(f"✅ {package} found in requirements.txt")
            else:
                print(f"❌ {package} missing from requirements.txt")
                all_good = False
                
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        all_good = False
    
    print(f"\n⚙️ Checking Django settings for Render:")
    try:
        # Check if settings file has Render configurations
        with open("servicesbladi/settings.py", "r") as f:
            settings_content = f.read()
            
        render_checks = [
            ("RENDER", "Render environment detection"),
            ("dj_database_url", "Database URL parsing"),
            ("RENDER_EXTERNAL_HOSTNAME", "Render hostname handling"),
            ("WhiteNoise", "Static files handling"),
            ("corsheaders", "CORS configuration")
        ]
        
        for check, description in render_checks:
            if check in settings_content:
                print(f"✅ {description} configured")
            else:
                print(f"⚠️ {description} might need attention")
                
    except FileNotFoundError:
        print("❌ settings.py not found")
        all_good = False
    
    print(f"\n🗄️ Checking app structure:")
    apps_to_check = [
        "accounts", "services", "custom_requests", "resources", 
        "messaging", "chatbot", "notifications"
    ]
    
    for app in apps_to_check:
        app_path = Path(app)
        if app_path.exists() and (app_path / "__init__.py").exists():
            print(f"✅ {app} app structure OK")
        else:
            print(f"❌ {app} app missing or incomplete")
            all_good = False
    
    print(f"\n📋 Deployment Readiness Summary:")
    if all_good:
        print("🎉 ✅ ALL CHECKS PASSED!")
        print("🚀 Your ServicesBladi project is 100% ready for Render.com!")
        print("\n📝 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Create PostgreSQL database on Render")
        print("3. Create Web Service on Render")
        print("4. Set environment variables from render.env.example")
        print("5. Deploy!")
        print(f"\n📖 See RENDER_DEPLOYMENT_GUIDE.md for detailed instructions")
    else:
        print("❌ Some issues found. Please fix them before deploying.")
        print("📖 Check RENDER_DEPLOYMENT_GUIDE.md for help")
        sys.exit(1)

if __name__ == "__main__":
    main()
