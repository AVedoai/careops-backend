#!/usr/bin/env python3
"""
CareOps Quick Start Script

This script will help you set up the CareOps backend quickly for development.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_prerequisites():
    """Check if required tools are installed"""
    required_tools = ['python', 'pip', 'redis-server']
    missing = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL,
                          check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing required tools: {', '.join(missing)}")
        print("Please install them before continuing.")
        return False
    
    print("✅ All prerequisites are installed")
    return True

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            subprocess.run(['cp', '.env.example', '.env'])
            print("📝 Created .env file from .env.example")
            print("⚠️  Please update the .env file with your actual configuration values")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def setup_database():
    """Setup database migrations"""
    print("🗄️  Setting up database...")
    try:
        # Generate initial migration if migrations directory is empty
        migrations_dir = Path('alembic/versions')
        if not any(migrations_dir.glob('*.py')):
            print("🔄 Generating initial migration...")
            subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Initial migration'], 
                          check=True)
        
        # Run migrations
        print("🔄 Running migrations...")
        subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        print("✅ Database setup complete")
        return True
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
        print("Make sure PostgreSQL is running and connection details in .env are correct")
        return False

def start_services():
    """Start the development services"""
    print("🚀 Starting CareOps backend...")
    print("📝 You can now:")
    print("   - Visit http://localhost:8000/docs for API documentation")
    print("   - Visit http://localhost:8000/health for health check")
    print("   - Use Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, 'manage.py', 'dev'])
    except KeyboardInterrupt:
        print("\\n👋 CareOps backend stopped")

def main():
    print("🏥 CareOps Backend Quick Start")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup failed, but you can continue manually")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Update DATABASE_URL in .env file")
        print("   3. Run: python manage.py migrate")
    
    print("\\n" + "=" * 40)
    print("✅ CareOps backend is ready!")
    print("\\nNext steps:")
    print("1. Start the development server: python manage.py dev")
    print("2. Start Celery worker (in another terminal): python manage.py worker")  
    print("3. Seed database with test data: python manage.py seed")
    print("\\nOr run all services with: python quickstart.py")

if __name__ == "__main__":
    main()