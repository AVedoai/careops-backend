#!/usr/bin/env python3
"""
Pre-deployment verification script
Run this before deploying to Railway to catch any issues
"""

import os
import subprocess
import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a required file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {filepath}")
    return exists

def check_requirements():
    """Check if all Python packages are installable"""
    print("\n📦 Checking Python requirements...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "check"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All packages compatible")
            return True
        else:
            print(f"❌ Package conflicts: {result.stdout + result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def check_env_template():
    """Check if environment template has all required variables"""
    print("\n🔧 Checking environment template...")
    required_vars = [
        "DATABASE_URL", "REDIS_URL", "SECRET_KEY", "SENDGRID_API_KEY",
        "TWILIO_ACCOUNT_SID", "SUPABASE_URL", "CORS_ORIGINS"
    ]
    
    try:
        with open(".env.template", "r") as f:
            content = f.read()
            missing = [var for var in required_vars if var not in content]
            if missing:
                print(f"❌ Missing variables in template: {missing}")
                return False
            else:
                print("✅ All required variables in template")
                return True
    except FileNotFoundError:
        print("❌ .env.template not found")
        return False

def main():
    print("🚀 CareOps Backend Pre-deployment Check")
    print("=" * 45)
    
    # Check required files
    print("\n📁 Checking required files...")
    files_to_check = [
        "Procfile",
        "requirements.txt", 
        "railway.json",
        "runtime.txt",
        ".dockerignore",
        ".env.template",
        "DEPLOYMENT.md"
    ]
    
    files_ok = all(check_file_exists(f) for f in files_to_check)
    
    # Check Python requirements
    packages_ok = check_requirements()
    
    # Check environment template
    env_ok = check_env_template()
    
    # Check if we're in a git repo
    print("\n📝 Checking git repository...")
    try:
        subprocess.run(["git", "status"], capture_output=True, check=True)
        print("✅ Git repository detected")
        git_ok = True
    except:
        print("❌ Not in a git repository or git not available")
        git_ok = False
    
    # Summary
    print("\n" + "=" * 45)
    all_checks = [files_ok, packages_ok, env_ok, git_ok]
    
    if all(all_checks):
        print("🎉 All pre-deployment checks passed!")
        print("\nNext steps:")
        print("1. Commit and push your code to GitHub")
        print("2. Create a new Railway project")
        print("3. Add PostgreSQL and Redis services") 
        print("4. Set environment variables from .env.template")
        print("5. Deploy and run health_check.py")
        print("\nSee DEPLOYMENT.md for detailed instructions.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        failed_checks = []
        if not files_ok:
            failed_checks.append("Missing required files")
        if not packages_ok:
            failed_checks.append("Package dependency issues")
        if not env_ok:
            failed_checks.append("Environment template issues")
        if not git_ok:
            failed_checks.append("Git repository not set up")
        
        print(f"Failed: {', '.join(failed_checks)}")
        sys.exit(1)

if __name__ == "__main__":
    main()