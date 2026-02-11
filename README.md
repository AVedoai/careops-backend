# CareOps Backend

A modern FastAPI-based backend for the CareOps business operations platform, designed to help small businesses manage customer communications, bookings, and workflow automation.

## Features

- **Authentication & Authorization**: JWT-based authentication with workspace isolation
- **Contact Management**: Customer contact database with conversation tracking
- **Booking System**: Service booking with calendar integration
- **Multi-channel Messaging**: Email and SMS communication via SendGrid and Twilio
- **Form Management**: Dynamic forms with file uploads and submissions
- **Inventory Tracking**: Basic inventory management with low-stock alerts
- **Automation Engine**: Celery-based background tasks for notifications and workflows
- **Integration Layer**: Extensible integration system for external services

## Technology Stack

- **FastAPI 0.104.1**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database with SQLAlchemy ORM
- **Redis**: Message broker for Celery task queue
- **Celery**: Background task processing
- **SendGrid**: Email delivery service
- **Twilio**: SMS messaging service
- **Alembic**: Database migration management
- **Docker**: Containerization for deployment

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd backend
python quickstart.py
```

The quickstart script will:
- Check prerequisites
- Install dependencies
- Create .env file from template
- Setup database migrations
- Start the development server

### 2. Manual Setup (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
python manage.py dev
```

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/careops

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Integrations
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Development Commands

Use the management script for common tasks:

```bash
# Database operations
python manage.py migrate      # Run migrations
python manage.py seed         # Seed test data

# Development servers
python manage.py dev          # Start API server
python manage.py worker       # Start Celery worker

# Utilities
python manage.py shell        # Interactive Python shell
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Architecture

### Directory Structure

```
app/
├── api/v1/           # API route handlers
├── services/         # Business logic layer
├── models/           # SQLAlchemy database models  
├── schemas/          # Pydantic request/response schemas
├── integrations/     # External service wrappers
├── utils/            # Utility functions
├── config.py         # Configuration management
├── database.py       # Database connection
└── main.py          # FastAPI application

tasks/               # Celery background tasks
scripts/             # Development scripts
alembic/             # Database migrations
```

### Key Components

1. **API Layer** (`api/v1/`): FastAPI routers handling HTTP requests
2. **Service Layer** (`services/`): Business logic separated from API concerns
3. **Data Layer** (`models/`): SQLAlchemy models defining database schema
4. **Integration Layer** (`integrations/`): Wrappers for external services
5. **Task Layer** (`tasks/`): Asynchronous background processing

## Database Schema

Core entities:
- **Users**: Authentication and user management
- **Workspaces**: Multi-tenant workspace isolation
- **Contacts**: Customer contact information
- **Conversations**: Message threads with contacts
- **Bookings**: Service appointments and scheduling
- **Services**: Offered services configuration
- **Forms**: Dynamic form definitions and submissions
- **Integrations**: External service configurations

## Background Tasks

Celery tasks handle:
- Email/SMS notifications
- Booking reminders
- Form submission processing
- Inventory alerts
- Automation rules

Start the worker: `python manage.py worker`

## Deployment

### Railway (Recommended)

The project includes Railway configuration (`railway.json`):

```bash
# Deploy to Railway
railway up
```

### Docker

```bash
# Build image
docker build -t careops-backend .

# Run container
docker run -p 8000:8000 --env-file .env careops-backend
```

### Environment Variables for Production

```bash
DATABASE_URL=postgresql://...     # Production database
REDIS_URL=redis://...             # Production Redis
SECRET_KEY=...                    # Strong production secret
DEBUG=false                       # Disable debug mode
ENVIRONMENT=production
```

## Testing

Run tests with pytest:

```bash
pip install pytest pytest-asyncio
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Check the [API documentation](http://localhost:8000/docs)
- Review the [issues page](../issues)
- Read the [project specification](../docs/specification.md)