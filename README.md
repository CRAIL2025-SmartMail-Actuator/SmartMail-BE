# 🧠 SmartMail

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> An intelligent email-processing backend built with FastAPI, featuring advanced vector search capabilities, email parsing, and comprehensive monitoring.

## 📦 Version

**Current Version:** `1.0.0`

## ✅ Project Overview

SmartMail is a cutting-edge email processing backend that leverages the power of artificial intelligence and modern web technologies. Built with FastAPI, it provides:

- **🔍 Semantic Email Search** - Advanced vector search capabilities using Qdrant
- **📧 Intelligent Email Parsing** - Automated email content extraction and processing
- **📊 Real-time Monitoring** - Comprehensive error tracking with Sentry integration
- **🚀 High Performance** - Asynchronous processing with FastAPI
- **🔒 Data Validation** - Robust input validation using Pydantic models

## 📌 Requirements

- **Python 3.10+**
- **Docker & Docker Compose**
- **Git** (for version control)

## ⚙️ Technologies Used

| Technology | Purpose | Version |
|------------|---------|---------|
| 🐍 **FastAPI** | Modern web framework | Latest |
| 🧬 **Pydantic** | Data validation & serialization | Latest |
| 🧱 **SQLAlchemy** | Object-Relational Mapping (ORM) | 2.0+ |
| 🔁 **Alembic** | Database migrations | Latest |
| 💥 **Sentry** | Error monitoring & performance tracking | Latest |
| 📬 **PostgreSQL** | Relational database | 15+ |
| 🔍 **Qdrant** | Vector search database for semantic search | Latest |

## 🛠️ Development Setup Instructions

### 1. 📥 Clone the Repository

```bash
git clone https://github.com/your-username/smartmail.git
cd smartmail
```

### 2. 📄 Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env_example .env
```

Update the `.env` file with your specific configuration values:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/smartmail

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Sentry Configuration (Optional)
SENTRY_DSN=your-sentry-dsn-here

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3. 🐳 Start Dependencies Using Docker Compose

Launch PostgreSQL and other services:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis (for caching)
- Any other configured services

### 4. 🚀 Start Qdrant Vector Database

If Qdrant is not included in your Docker Compose setup, start it separately:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. 📦 Install Python Dependencies

Create a virtual environment and install requirements:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. 🗃️ Run Database Migrations

Initialize and run database migrations:

```bash
alembic upgrade head
```

### 7. 🏃‍♂️ Run the Application

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Optional Integrations

### Sentry Error Monitoring

To enable comprehensive error monitoring and performance tracking:

1. Sign up for a [Sentry](https://sentry.io) account
2. Create a new project for your FastAPI application
3. Copy the DSN from your Sentry project settings
4. Set the `SENTRY_DSN` environment variable in your `.env` file:

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Additional Integrations

- **📧 Email Providers**: Configure SMTP settings for email notifications
- **🔐 Authentication**: JWT token-based authentication (already configured)
- **📊 Monitoring**: Integration with monitoring tools like Prometheus/Grafana

## 🧪 Running Tests

Execute the test suite to ensure everything is working correctly:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api/test_emails.py

# Run tests in verbose mode
pytest -v
```

## 📚 API Usage Examples

### Send Email for Processing

```bash
curl -X POST "http://localhost:8000/api/v1/emails/process" \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Important Meeting",
       "content": "Please join us for the quarterly review meeting.",
       "sender": "manager@company.com"
     }'
```

### Search Emails (Semantic Search)

```bash
curl -X GET "http://localhost:8000/api/v1/search?query=meeting%20quarterly&limit=10"
```

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

## 🚀 Production Deployment

### Using Docker

```bash
# Build the image
docker build -t smartmail:latest .

# Run the container
docker run -p 8000:8000 --env-file .env smartmail:latest
```

### Environment Variables for Production

```env
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db:5432/smartmail
SENTRY_DSN=your-production-sentry-dsn
SECRET_KEY=your-super-secure-secret-key
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **📧 Email**: cogninesmartmail@gmail.com
