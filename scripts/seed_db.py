#!/usr/bin/env python3
"""
Script to seed the database with sample data for development

Usage:
    python scripts/seed_db.py
"""

import sys
from pathlib import Path
from datetime import datetime, date, time, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_db
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.models.contact import Contact
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.integration import Integration
from app.models.automation_rule import AutomationRule
from app.utils.security import get_password_hash


def create_sample_data():
    """Create sample data for development"""
    db = next(get_db())
    
    try:
        # Create sample workspace
        workspace = Workspace(
            name="Wellness Spa",
            slug="wellness-spa",
            address="123 Wellness Street, Relaxation City, RC 12345",
            timezone="America/New_York",
            contact_email="info@wellness-spa.com",
            contact_phone="+1-555-0123",
            is_active=True,
            onboarding_completed=True,
            onboarding_step=5
        )
        db.add(workspace)
        db.flush()
        
        # Create owner user
        owner = User(
            email="owner@wellness-spa.com",
            hashed_password=get_password_hash("password123"),
            full_name="Sarah Johnson",
            role=UserRole.OWNER,
            workspace_id=workspace.id,
            is_active=True,
            can_manage_inbox=True,
            can_manage_bookings=True,
            can_view_forms=True,
            can_view_inventory=True
        )
        db.add(owner)
        
        # Create staff user
        staff = User(
            email="staff@wellness-spa.com",
            hashed_password=get_password_hash("password123"),
            full_name="Mike Wilson",
            role=UserRole.STAFF,
            workspace_id=workspace.id,
            is_active=True,
            can_manage_inbox=True,
            can_manage_bookings=True,
            can_view_forms=False,
            can_view_inventory=False
        )
        db.add(staff)
        
        # Create sample services
        services_data = [
            {
                "name": "60-Minute Swedish Massage",
                "slug": "60-min-swedish-massage",
                "description": "Relaxing full-body massage to relieve tension and stress",
                "duration_minutes": 60,
                "location": "Massage Room 1",
                "availability": {
                    "monday": ["09:00-12:00", "13:00-17:00"],
                    "tuesday": ["09:00-17:00"],
                    "wednesday": ["09:00-17:00"],
                    "thursday": ["09:00-17:00"],
                    "friday": ["09:00-15:00"],
                    "saturday": ["10:00-16:00"],
                    "sunday": []
                }
            },
            {
                "name": "90-Minute Deep Tissue Massage",
                "slug": "90-min-deep-tissue-massage",
                "description": "Therapeutic massage targeting muscle knots and tension",
                "duration_minutes": 90,
                "location": "Massage Room 2",
                "availability": {
                    "monday": ["10:00-16:00"],
                    "tuesday": ["10:00-16:00"],
                    "wednesday": ["10:00-16:00"],
                    "thursday": ["10:00-16:00"],
                    "friday": ["10:00-14:00"],
                    "saturday": [],
                    "sunday": []
                }
            },
            {
                "name": "Facial Treatment",
                "slug": "facial-treatment",
                "description": "Rejuvenating facial with organic products",
                "duration_minutes": 75,
                "location": "Treatment Room A",
                "availability": {
                    "monday": ["09:00-17:00"],
                    "tuesday": ["09:00-17:00"],
                    "wednesday": ["09:00-17:00"],
                    "thursday": ["09:00-17:00"],
                    "friday": ["09:00-17:00"],
                    "saturday": ["10:00-16:00"],
                    "sunday": []
                }
            }
        ]
        
        services = []
        for service_data in services_data:
            service = Service(**service_data, workspace_id=workspace.id)
            db.add(service)
            services.append(service)
        
        db.flush()
        
        # Create sample contacts
        contacts_data = [
            {
                "full_name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0101",
                "preferred_channel": "email"
            },
            {
                "full_name": "Emily Davis",
                "email": "emily.davis@email.com",
                "phone": "+1-555-0102",
                "preferred_channel": "email"
            },
            {
                "full_name": "Michael Brown",
                "email": "michael.brown@email.com",
                "phone": "+1-555-0103",
                "preferred_channel": "sms"
            },
            {
                "full_name": "Lisa Wilson",
                "email": "lisa.wilson@email.com",
                "phone": "+1-555-0104",
                "preferred_channel": "email"
            }
        ]
        
        contacts = []
        for contact_data in contacts_data:
            contact = Contact(**contact_data, workspace_id=workspace.id)
            db.add(contact)
            contacts.append(contact)
        
        db.flush()
        
        # Create sample bookings
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        bookings_data = [
            {
                "contact_id": contacts[0].id,
                "service_id": services[0].id,
                "booking_date": tomorrow,
                "booking_time": time(10, 0),
                "status": BookingStatus.CONFIRMED,
                "notes": "First time client"
            },
            {
                "contact_id": contacts[1].id,
                "service_id": services[1].id,
                "booking_date": next_week,
                "booking_time": time(14, 0),
                "status": BookingStatus.CONFIRMED,
                "notes": "Regular client"
            },
            {
                "contact_id": contacts[2].id,
                "service_id": services[2].id,
                "booking_date": today + timedelta(days=3),
                "booking_time": time(11, 0),
                "status": BookingStatus.PENDING,
                "notes": "Needs confirmation"
            }
        ]
        
        for booking_data in bookings_data:
            booking = Booking(**booking_data, workspace_id=workspace.id)
            db.add(booking)
        
        # Create sample automation rules
        rules_data = [
            {
                "name": "Welcome New Contacts",
                "event_type": "contact_created",
                "action_type": "send_email",
                "config": {
                    "template": "welcome_email",
                    "subject": "Thanks for reaching out!",
                    "delay_minutes": 0
                },
                "is_active": True
            },
            {
                "name": "Booking Confirmation",
                "event_type": "booking_created",
                "action_type": "send_booking_confirmation",
                "config": {
                    "delay_minutes": 0
                },
                "is_active": True
            },
            {
                "name": "24h Appointment Reminder",
                "event_type": "booking_created",
                "action_type": "schedule_reminder",
                "config": {
                    "hours_before": 24,
                    "template": "booking_reminder"
                },
                "is_active": True
            }
        ]
        
        for rule_data in rules_data:
            rule = AutomationRule(**rule_data, workspace_id=workspace.id)
            db.add(rule)
        
        # Create sample integration (placeholder)
        integration = Integration(
            workspace_id=workspace.id,
            type="email",
            provider="sendgrid",
            credentials={
                "api_key": "your_sendgrid_api_key_here",
                "from_email": "noreply@wellness-spa.com"
            },
            is_active=False,  # Disabled until real credentials are added
            test_status="not_tested"
        )
        db.add(integration)
        
        db.commit()
        print("✅ Sample data created successfully!")
        print(f"🏢 Workspace: {workspace.name} ({workspace.slug})")
        print(f"👤 Owner: {owner.email} (password: password123)")
        print(f"👤 Staff: {staff.email} (password: password123)")
        print(f"🛎️ Services: {len(services)} created")
        print(f"👥 Contacts: {len(contacts)} created")
        print(f"📅 Bookings: {len(bookings_data)} created")
        print(f"🤖 Automation rules: {len(rules_data)} created")
        print()
        print("🌐 You can now:")
        print(f"   - Access public booking page: /public/booking/{workspace.slug}/60-min-swedish-massage")
        print(f"   - Access public contact form: /public/contact-form/{workspace.slug}")
        print("   - Login to dashboard with owner credentials")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("🌱 Seeding database with sample data...")
    create_sample_data()