# Construction Labour Management System

A FastAPI + PostgreSQL construction labour management system with one external API key only: `OPENAI_API_KEY`.

## Features
- Authentication
- Labour CRUD
- Construction sites
- Labour-site assignments
- Attendance
- Salary estimation
- Advance tracking
- Payments
- Overtime
- Dashboard
- CSV report
- AI labour assistant
- Responsive mobile UI
- WhatsApp/API-free messaging can be added later without an API key

## Setup (Windows)

1. Install Python 3.11+ and PostgreSQL.
2. Create database:
   `CREATE DATABASE construction_labour_db;`
3. Create and activate environment:
   `python -m venv venv`
   `venv\Scripts\activate`
4. Install:
   `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set PostgreSQL password and the ONE OpenAI API key.
6. Run:
   `uvicorn app.main:app --reload`
7. Open http://127.0.0.1:8000
8. Swagger: http://127.0.0.1:8000/docs

SQLite is used automatically if DATABASE_URL is omitted, which is useful for a quick local demo. PostgreSQL is recommended for submission.

## One API key policy
Only `OPENAI_API_KEY` is used. There are no Gemini, Groq, Weather, Maps, WhatsApp, or other third-party API keys.
