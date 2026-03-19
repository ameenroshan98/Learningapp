# Care n Cure Group Internal Learning Platform MVP

A working MVP for a performance-driven internal learning platform for Care n Cure Group. The app supports secure login, role-based dashboards, department-focused courses, randomized MCQ assessments, progress tracking, analytics, CSV export, notifications, and basic gamification.

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy
- **Frontend:** Server-served responsive HTML/CSS/JavaScript dashboard
- **Database:** SQLite for local MVP (`learning_platform.db`)
- **Authentication:** JWT access token

## Project Structure

```text
app/
  auth.py                # JWT auth and role guards
  database.py            # SQLAlchemy engine/session setup
  main.py                # FastAPI app, API endpoints, static serving
  models.py              # Database schema models
  schemas.py             # Request/response models
  seed.py                # Sample departments, users, courses, quizzes, badges
  services/analytics.py  # Employee/manager/admin dashboard metrics
  static/
    css/styles.css       # Responsive dashboard styling
    js/app.js            # Login, dashboard, course, and quiz interactions
  templates/index.html   # Login + dashboard + courses + quiz views
requirements.txt         # Python dependencies
README.md                # Run guide and feature summary
```

## Database Schema Overview
- `departments`: Department catalog (Pharmacy, FMCG, Sales, Operations)
- `users`: Employees, managers, admins with unique employee IDs and department assignment
- `courses`: Department + skill-level based courses
- `modules`: Learning modules inside courses with text/video/pdf-compatible fields
- `questions`: Question bank for randomized MCQs
- `course_assignments`: Tracks status, progress, score, deadlines, and time spent
- `quiz_attempts`: Stores assessment outcomes
- `notifications`: In-app notification feed
- `badge_awards`: Bonus gamification points and badges

## API Endpoints

### Auth
- `POST /api/auth/login` — JWT login using email/password
- `GET /api/me` — Current user info

### Dashboard / Analytics
- `GET /api/dashboard` — Role-aware employee/manager/admin analytics
- `GET /api/reports/export` — CSV export for manager/admin

### Courses
- `GET /api/courses` — List available courses + assignment status
- `GET /api/courses/{course_id}` — Course details + modules
- `POST /api/courses` — Admin create course
- `PUT /api/courses/{course_id}` — Admin update course
- `DELETE /api/courses/{course_id}` — Admin delete course
- `POST /api/assignments` — Admin/manager assign course

### Assessments
- `GET /api/modules/{module_id}/quiz` — Randomized question payload
- `POST /api/quiz/submit` — Auto-scored assessment with pass/fail logic

### Utility
- `GET /api/seed-users` — Demo credentials

## Frontend Pages / Views
- **Login:** Secure email/password login
- **Dashboard:** Employee, manager, or admin metrics with notifications and chart-style analytics
- **Course View:** Department-based course cards and module details
- **Quiz View:** Randomized MCQ quiz submission with scoring feedback

## Sample Data
Seeded automatically on startup:
- Departments: Pharmacy, FMCG, Sales, Operations
- Users: 1 Admin, 1 Manager, 3 Employees
- Courses: 4 sample courses
- Modules: 1 module per course for MVP
- Question bank: 1 seeded MCQ per module
- Notifications and badge awards

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Default Demo Credentials
- Admin: `admin@carencure.com` / `Admin@123`
- Manager: `manager@carencure.com` / `Manager@123`
- Employee: `sara@carencure.com` / `Employee@123`

## Major Components Explained
- **Authentication layer:** Handles password hashing, JWT creation, and role-based route protection.
- **Learning content engine:** Organizes courses by department and skill level, with modules that can point to text, PDF, or video content.
- **Assessment engine:** Pulls module questions from a question bank, randomizes them, auto-scores attempts, and applies pass/fail logic.
- **Progress tracker:** Stores course start/completion state, scores, deadlines, and time spent for each assignment.
- **Analytics service:** Builds role-aware metrics for employees, managers, and admins, including completion and leaderboard data.
- **Notifications + gamification:** Generates in-app alerts and badge points for completion milestones.
