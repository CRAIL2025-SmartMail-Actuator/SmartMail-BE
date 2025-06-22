# Email Categorizer Application

An intelligent email categorization system that automatically processes incoming emails, categorizes them using GrokGPT AI, and provides automated responses. Built with Flask, PostgreSQL, and LangChain.

## Features

- ** AI-Powered Categorization**: Uses GroqGPT to intelligently categorize emails into Customer Support, Marketing, or Others
- ** Real-time Email Monitoring**: Continuously monitors IMAP inbox for new emails
- ** Automated Responses**: Sends categorization confirmations to email senders
- ** Statistics Dashboard**: Track email volumes and category distributions via REST API
- ** Docker Support**: Full containerization with Docker Compose
- ** PostgreSQL Integration**: Robust database storage with proper indexing
- ** Modern Python Stack**: Uses UV package manager and modern dependencies
- ** Comprehensive Logging**: Detailed logging for monitoring and debugging

## Project Structure

```
smartmail-be/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models
│   ├── email_service.py      # Email processing service
│   ├── categorizer.py        # GrokGPT integration
│   └── routes.py             # API endpoints
├── migrations/
│   └── init.sql              # Database initialization
├── docker-compose.yml        # Container orchestration
├── Dockerfile               # Application container
├── pyproject.toml           # Dependencies and project config
├── main.py                  # Application entry point
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Email account with IMAP access (Gmail recommended)
- GroqGPT API key

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd email-categorizer
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/email_categorizer

# Email Configuration (Gmail example)
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_USE_SSL=true

# GrokGPT Configuration
GROK_API_KEY=your-grok-api-key
GROK_BASE_URL=https://api.x.ai/v1

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secure-secret-key-here
```

### 3. Gmail Setup (Recommended)

If using Gmail, you need to set up App Passwords:

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security → App Passwords
3. Generate a new app password for "Mail"
4. Use this app password (not your regular password) in `EMAIL_PASSWORD`

## Running the Application

### Option 1: Docker Compose (Recommended)

This is the easiest way to get started:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

This will start:

- The Flask application on `http://localhost:5000`
- PostgreSQL database on `localhost:5432`
- Automatic email monitoring

### Option 2: Local Development

If you prefer to run locally:

```bash
# Install dependencies
uv pip install -r pyproject.toml
```

## API Endpoints

### Health Check

```
GET /
```

Returns application status.

### Email Management

```
GET /api/emails
```

Retrieve all emails with optional filtering:

- `?category=Customer Support` - Filter by category
- `?sender=example@email.com` - Filter by sender
- `?limit=50&offset=0` - Pagination

```
GET /api/emails/<id>
```

Get specific email by ID.

### Statistics

```
GET /api/stats
```

Get email categorization statistics.

### Manual Controls

```
POST /api/fetch-emails
```

Manually trigger fetching all existing emails from inbox.

```
POST /api/start-monitoring
```

Start real-time email monitoring.

```
POST /api/stop-monitoring
```

Stop email monitoring.

```
GET /api/categories
```

Get available email categories.

## Usage Examples

### Get all Customer Support emails

```bash
curl "http://localhost:5000/api/emails?category=Customer%20Support"
```

### Get statistics

```bash
curl "http://localhost:5000/api/stats"
```

### Manually process all emails

```bash
curl -X POST "http://localhost:5000/api/fetch-emails"
```

## Email Categories

The system categorizes emails into three categories:

1. **Customer Support** - Help requests, issue reports, technical problems, complaints
2. **Marketing** - Promotional emails, newsletters, advertisements, product announcements
3. **Others** - Personal messages, administrative emails, confirmations, uncategorized content

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Access database
docker-compose exec db psql -U emailuser -d email_categorizer

# Access application shell
docker-compose exec app bash
```

### Application Logs

```bash
# View real-time logs
docker-compose logs -f app

# View database logs
docker-compose logs -f db
```
