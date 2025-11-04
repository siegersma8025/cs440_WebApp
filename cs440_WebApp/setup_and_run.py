#!/usr/bin/env python
"""
Django Development Setup Script
Handles all setup tasks and starts the development server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=False, text=True)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting Django Development Environment Setup...")
    print("=" * 60)
    
    # Get the Django project directory
    script_dir = Path(__file__).parent
    django_dir = script_dir / "cs440WebApp"
    
    # Check if manage.py exists
    manage_py = django_dir / "manage.py"
    if not manage_py.exists():
        print(f"❌ ERROR: manage.py not found at {manage_py}")
        print("Make sure you're running this from the correct directory.")
        sys.exit(1)
    
    print(f"📁 Django project directory: {django_dir}")
    
    # Step 1: Install/Upgrade pip
    print("\n🔧 Step 1: Ensuring pip is up to date...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Step 2: Install requirements if they exist
    requirements_file = django_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"\n🔧 Step 2: Installing requirements from {requirements_file}")
        run_command(f"python -m pip install -r requirements.txt", 
                   "Installing Python dependencies", cwd=django_dir)
    else:
        print("\n⚠️  Step 2: No requirements.txt found, skipping dependency installation")
    
    # Step 3: Run migrations
    print("\n🔧 Step 3: Running database migrations...")
    success = run_command("python manage.py migrate", 
                         "Running database migrations", cwd=django_dir)
    
    if not success:
        print("\n⚠️  Migration failed, but continuing...")
    
    # Step 4: Collect static files (if needed)
    print("\n🔧 Step 4: Collecting static files...")
    run_command("python manage.py collectstatic --noinput", 
               "Collecting static files", cwd=django_dir)
    
    # Step 5: Check for superuser (optional)
    print("\n🔧 Step 5: Checking Django setup...")
    run_command("python manage.py check", "Running Django system checks", cwd=django_dir)
    
    # Final step: Start the development server
    print("\n" + "="*60)
    print("🎉 Setup complete! Starting Django development server...")
    print("🌐 Your app will be available at: http://127.0.0.1:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    time.sleep(2)  # Give user time to read the message
    
    try:
        # Start the Django development server
        subprocess.run(["python", "manage.py", "runserver", "127.0.0.1:8000"], 
                      cwd=django_dir, check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()