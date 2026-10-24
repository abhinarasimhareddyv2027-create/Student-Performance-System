# Student & Employee Performance Management System

Browser-based student and employee management using a React/TypeScript frontend and a Python FastAPI backend. The existing CustomTkinter app and profile services are retained; the web API reuses their SQLAlchemy models, authentication, and profile rules.

## Technology

- Frontend: React 19, TypeScript, Vite, Tailwind CSS, Radix/shadcn-style primitives, React Router, React Hook Form, Zod, Lucide, Recharts, and Sonner.
- Backend: FastAPI, Pydantic 2, SQLAlchemy 2, Argon2 password verification, NumPy, and Pandas.
- Database: SQLite by default; PostgreSQL through `SPS_DATABASE_URL` for deployment.

## Codespaces: Run the Web App

Run the API and UI in separate terminals. Keep forwarded ports **8000** and **5173 Private**. Do not forward the database port.

1. Activate the project's Python environment and install backend dependencies:

	```bash
	source .venv/bin/activate
	pip install -r requirements.txt
	```

2. Start FastAPI in terminal 1 from the repository root:

	```bash
	uvicorn backend.main:app --host 0.0.0.0 --port 8000
	```

	Forward port `8000` privately. `GET /api/health` should return `{"status":"ok"}`. The app creates missing tables and applies its additive profile-column update; it does not delete the database.

3. Install and start Vite in terminal 2:

	```bash
	cd frontend
	cp .env.example .env.local
	npm ci
	npm run dev -- --host 0.0.0.0
	```

	Forward port `5173` privately and open it in the browser. Vite proxies `/api` requests to `http://127.0.0.1:8000`; both app requests and the session cookie use the forwarded frontend origin. Vite's SPA fallback supports refreshing nested routes.

4. Create the initial administrator only if the server database has no users. From the repository root in a third terminal:

	```bash
	python main.py --setup-admin
	```

	Enter a username and password when prompted. No default credentials are created. Do not commit `.env` files or real credentials.

### Environment and Direct API Forwarding

Copy `.env.example` to `.env` and configure `SPS_JWT_SECRET_KEY` with a strong random value before deployment. `SPS_COOKIE_SECURE` defaults on in Codespaces and off for local HTTP development. Set `SPS_DATABASE_URL` to a PostgreSQL SQLAlchemy URL to use PostgreSQL. `SPS_CORS_ORIGINS` accepts comma-separated trusted origins.

The Vite proxy is recommended. To call a forwarded backend URL directly, set `VITE_API_BASE_URL` in `frontend/.env.local` to that URL ending in `/api`, and add the exact forwarded frontend origin to `SPS_CORS_ORIGINS`. Codespaces frontend origins of the form `https://<codespace>-5173.app.github.dev` are also allowed. Never make forwarded ports public unless the deployment owner explicitly requires it.

## Local Development

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

The legacy Python desktop entry point remains available with `python main.py`; it is not the browser-app startup command.

## Implemented Modules

- Live dashboard cards and Recharts trends, subject averages, and grade distribution from API analytics; no fabricated live values.
- Student and employee create/read/update/archive, search, filters, and CSV exports. Employee users can access only their linked profile and own scoped data.
- Departments, courses, subjects, examinations, marks, student/employee attendance, leave, student activities, employee tasks/reviews, analytics, CSV reports, users/roles, and settings are exposed through authenticated API-backed screens.
- Argon2 passwords, expiring HttpOnly session cookies, role checks, CORS configuration, audit events, SQLite/PostgreSQL connection support, and input validation.

Some secondary academic screens currently provide list/create/archive workflows rather than full edit/archive for every entity. CSV is implemented; PDF and Excel export are not. Profile image storage, password reset/MFA, Alembic migrations, backup/restore, and production deployment hardening remain unfinished. Student course/department are profile fields until reference-data foreign keys are migrated. Performance reviews remain explicit manager feedback and optional documented rubric scores, not automatic employee ratings.

Mark states distinguish pending, absent, and entered zero. Academic percentages use entered marks only; pass rate uses entered marks as its denominator. Attendance excludes excused/leave records. Empty denominators return unavailable metrics rather than zero.

## Tests and Build

Backend tests use temporary SQLite databases and fictional records:

```bash
source .venv/bin/activate
pytest -q
```

Frontend checks:

```bash
cd frontend
npm run typecheck
npm run build
```

API docs are available from FastAPI at `/docs` on port `8000`.

## Screenshots

Add screenshots after opening the Codespaces browser UI and verifying it with records. No screenshots are included yet.

## Team and License

Add team member names and verified contributions. No license has been selected; choose one before redistribution.