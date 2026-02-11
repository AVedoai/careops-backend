#!/usr/bin/env python3
"""
CareOps Backend Management Script

Usage:
    python manage.py migrate      # Run database migrations
    python manage.py seed         # Seed the database with initial data
    python manage.py dev          # Start development server
    python manage.py worker       # Start Celery worker
    python manage.py shell        # Start interactive shell
"""

import sys
import os
import subprocess
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("✅ Migrations completed!")

def seed_database():
    """Seed the database with initial data"""
    print("🌱 Seeding database...")
    subprocess.run([sys.executable, "scripts/seed_db.py"], check=True)
    print("✅ Database seeded!")

def start_dev_server():
    """Start development server"""
    print("🚀 Starting development server...")
    subprocess.run([sys.executable, "scripts/dev_server.py"], check=True)

def start_worker():
    """Start Celery worker"""
    print("👷 Starting Celery worker...")
    subprocess.run([sys.executable, "scripts/run_worker.py"], check=True)

def start_shell():
    """Start interactive Python shell with app context"""
    print("🐍 Starting interactive shell...")
    try:
        import IPython
    except ImportError:
        print("❌ IPython not installed. Install with: pip install ipython")
        return
    
    from app.database import get_db
    from app.models import user, workspace, contact, booking, conversation, service, form, integration, alert, message, inventory
    
    print("Available imports:")
    print("  - All models from app.models")
    print("  - get_db() function")
    
    IPython.start_ipython(argv=[], user_ns={
        'get_db': get_db,
        **{name: obj for name, obj in globals().items() 
           if name.startswith(('User', 'Workspace', 'Contact', 'Booking', 
                             'Conversation', 'Service', 'Form', 'Integration', 
                             'Alert', 'Message', 'Inventory'))}
    })

def show_help():
    """Show help message"""
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'migrate': run_migrations,
        'seed': seed_database,
        'dev': start_dev_server,
        'worker': start_worker,
        'shell': start_shell,
        'help': show_help,
        '--help': show_help,
        '-h': show_help,
    }
    
    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()