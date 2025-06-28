# 📦 FastAPI Email Categorizer

A FastAPI application that processes and categorizes emails using external APIs, stores them in PostgreSQL, and provides REST endpoints.

---

## 🚀 Features

- 🔥 FastAPI + Uvicorn (hot-reload in development)
- 📩 Email parsing and categorization
- 🧠 AI-based processing via Grok API
- 🐘 PostgreSQL for persistence
- 🐳 Docker-ready
- 🔐 Environment-based configuration

---

## 📁 Project Structure

.
│── main.py
├── database.py
├── models.py
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

---

## 🧑‍💻 Local Development (without Docker)

> ⚠️ Requires PostgreSQL running locally at `localhost:5432`  
> Make sure `.env` has a valid `DATABASE_URL` pointing to your local DB.

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/email-categorizer.git
cd email-categorizer
2. Create Virtual Environment
bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install Requirements
bash
Copy
Edit
pip install -r requirements.txt
4. Create .env
env
Copy
Edit
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/email_categorizer
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_password
EMAIL_USE_SSL=True
GROK_API_KEY=your_grok_api_key
SECRET_KEY=your_secret_key
5. Run the App
bash
Copy
Edit
uvicorn main:app --reload
Visit: http://localhost:8000/docs

🐳 Run with Docker
PostgreSQL will be started in a container.

1. Build and Start
bash
Copy
Edit
docker-compose up --build
2. Visit the App
API: http://localhost:8000

Swagger Docs: http://localhost:8000/docs

🛠️ Environment Variables
Make sure your .env file contains:

env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/email_categorizer  # or asyncpg for async SQLAlchemy

In Docker, these are injected via docker-compose.yml.

🐘 Local PostgreSQL DB Setup (if not using Docker)
You can install PostgreSQL locally via:

Linux: sudo apt install postgresql

macOS: brew install postgresql

Windows: Download PostgreSQL installer

Then create a DB:

bash
Copy
Edit
createdb email_categorizer
Ensure credentials match the DATABASE_URL in your .env.

✅ Requirements
txt
Copy
Edit
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
python-dotenv
📫 API Endpoints
GET /: Health check

POST /emails/: Submit and categorize email

GET /emails/: List emails

GET /emails/{id}: Get single email

🔐 Security Notes
Do not hardcode sensitive data.

Use secrets in .env and never commit them to version control.

🧼 Clean Up
bash
docker-compose down -v  # Stops containers and removes volumes
deactivate               # Exit virtual environment
📜 License
MIT License

