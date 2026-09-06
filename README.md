# Smart Job Tracker

A full-stack job application tracking platform with multi-user authentication,
a relational data model with status-change history, a REST API supporting
search/filter/pagination/analytics, an automated test suite, and a Docker +
Jenkins CI/CD pipeline.

## Overview

Smart Job Tracker lets a user sign up, log in, and manage their job
applications through their full lifecycle — from Wishlist through Applied,
Interview, and Offer/Rejected/Withdrawn — with every status change recorded
in an audit trail. The system is split into three layers: a static
HTML/CSS/JS frontend, a Flask REST API backend, and a PostgreSQL database,
each running in its own Docker container.

## Architecture

```
┌─────────────┐      HTTPS/JSON      ┌──────────────────┐      SQL      ┌────────────┐
│  Frontend   │  ───────────────►    │   Flask REST API │  ───────────► │ PostgreSQL │
│ HTML/CSS/JS │  ◄───────────────    │  (JWT-protected)  │  ◄─────────── │  Database  │
└─────────────┘   nginx (Docker)     └──────────────────┘   Docker net  └────────────┘
                                              │
                                              ▼
                                     Jenkins CI/CD pipeline
                                (lint → pytest → docker build →
                                     push → deploy)
```

- **Frontend** — plain HTML/CSS/JS, served as static files by nginx. It
  communicates with the backend entirely through `fetch()` calls to the REST
  API.
- **Backend** — Flask, structured as an application factory with blueprints
  (`auth`, `applications`) rather than a single monolithic file.
- **Database** — SQLAlchemy ORM models; SQLite for local development,
  PostgreSQL in Docker/production, controlled by a single `DATABASE_URL`
  environment variable.
- **Auth** — JWT access + refresh tokens (Flask-JWT-Extended) with bcrypt
  password hashing. Every application record is scoped to its owning user at
  the database query level.
- **Testing** — pytest with fixtures and an in-memory SQLite database,
  covering authentication, CRUD, authorization boundaries, filtering,
  pagination, and analytics.
- **CI/CD** — a Jenkins declarative pipeline that installs dependencies, runs
  pytest with coverage, builds Docker images for both services, and
  pushes/deploys them on the `main` branch.

## Data model

| Table | Purpose |
|---|---|
| `users` | Account credentials (hashed password), one row per user |
| `applications` | One row per job application: company, role, status, dates, notes |
| `status_history` | Append-only log of every status change per application |

Application statuses: `Wishlist → Applied → OA_Scheduled → Interview → Offer / Rejected / Withdrawn`

## Features

- Email/password signup and login with JWT access + refresh tokens
- Per-user data isolation, enforced at the query layer and covered by tests
- Full CRUD on applications, plus an automatic status-change audit trail
- Search by company/role, filter by status, sort, and pagination on the API
- An analytics endpoint returning total applications, response rate, offer
  rate, and upcoming interviews
- CSV export of all applications
- Three frontend views: Overview (stats dashboard), Pipeline Board
  (kanban-style by status), and All Applications (searchable/filterable
  table)
- Rate limiting on authentication endpoints, centralized error handlers, and
  input validation with structured error responses

## Project structure

```
smart-job-tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # application factory
│   │   ├── config.py         # dev/test/prod configuration
│   │   ├── extensions.py     # db, jwt, bcrypt, cors, limiter
│   │   ├── models.py         # User, Application, StatusHistory
│   │   ├── schemas.py        # marshmallow request validation
│   │   ├── auth.py           # /api/auth/* blueprint
│   │   └── routes.py         # /api/applications/* blueprint
│   ├── tests/                # pytest suite (29 tests, ~97% coverage)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── index.html            # login / register
│   ├── dashboard.html        # overview / board / list views
│   ├── css/style.css
│   ├── js/api.js             # fetch wrapper with token refresh
│   ├── js/auth.js
│   ├── js/dashboard.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml        # backend + postgres + frontend
├── Jenkinsfile                # CI/CD pipeline
└── .env.example
```

## Running locally (without Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=development
python run.py                 # http://localhost:5000

# Frontend (separate terminal)
cd frontend
python -m http.server 8080    # http://localhost:8080
```

Open `http://localhost:8080`, create an account, and start adding
applications.

## Running with Docker

```bash
cp .env.example .env          # fill in real secrets
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:5000/api
- Postgres: localhost:5432

## Running the tests

```bash
cd backend
pip install -r requirements.txt
pytest                        # runs with coverage (see pytest.ini)
```

The suite covers registration/login validation, duplicate-email handling,
token refresh, full CRUD on applications, the per-user data isolation
boundary, status-history recording, search/filter/pagination, analytics
calculations, and CSV export.

## CI/CD pipeline

The Jenkinsfile defines the following stages:

1. **Checkout** — pulls the repository
2. **Install & Lint** — installs Python dependencies, runs flake8
3. **Test** — runs pytest with coverage, publishes JUnit results
4. **Build** — builds backend and frontend Docker images
5. **Push** (main branch only) — pushes images to Docker Hub
6. **Deploy** (main branch only) — pulls and restarts containers via
   `docker compose`

Builds and deployments only proceed if the test stage passes.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create an account, returns tokens |
| POST | `/api/auth/login` | Log in, returns tokens |
| POST | `/api/auth/refresh` | Exchange a refresh token for a new access token |
| GET | `/api/applications?status=&q=&page=&per_page=&sort=` | List/search/filter applications |
| POST | `/api/applications` | Create an application |
| GET | `/api/applications/<id>` | Get one application with its status history |
| PUT | `/api/applications/<id>` | Update an application (records status change) |
| DELETE | `/api/applications/<id>` | Delete an application |
| GET | `/api/applications/analytics/summary` | Dashboard statistics |
| GET | `/api/applications/export/csv` | Download all applications as CSV |
