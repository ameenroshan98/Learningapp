import csv
import io
import random
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from .auth import create_access_token, get_current_user, require_roles, verify_password
from .database import Base, engine, get_db, SessionLocal
from .models import Course, CourseAssignment, Department, Module, Notification, Question, QuizAttempt, User, BadgeAward
from .schemas import AssignmentCreate, CourseCreate, LoginRequest, QuizSubmission, Token
from .seed import seed_data
from .services.analytics import admin_dashboard, employee_dashboard, manager_dashboard

app = FastAPI(title="Care n Cure Learning Platform")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
PASS_SCORE = 70


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE_DIR / "templates" / "index.html").read_text()


@app.post("/api/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.department)).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "employee_id": user.employee_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "department": user.department.name,
        },
    }


@app.get("/api/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.full_name, "role": current_user.role}


@app.get("/api/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    base = {
        "user": {
            "id": current_user.id,
            "name": current_user.full_name,
            "role": current_user.role,
            "department": current_user.department.name,
            "employee_id": current_user.employee_id,
        },
        "notifications": [
            {"id": n.id, "message": n.message, "read": n.is_read} for n in current_user.notifications[-5:]
        ],
        "leaderboard": [
            {"name": u.full_name, "department": u.department.name, "points": sum(b.points for b in u.badges)}
            for u in db.query(User).options(joinedload(User.department), joinedload(User.badges)).all()
        ],
    }
    if current_user.role == "Employee":
        base["metrics"] = employee_dashboard(db, current_user)
    elif current_user.role == "Manager":
        base["metrics"] = manager_dashboard(db, current_user)
    else:
        base["metrics"] = admin_dashboard(db)
    return base


@app.get("/api/courses")
def list_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignments = {a.course_id: a for a in db.query(CourseAssignment).filter(CourseAssignment.employee_id == current_user.id).all()}
    courses = db.query(Course).options(joinedload(Course.department), joinedload(Course.modules)).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "department": c.department.name,
            "skill_level": c.skill_level,
            "estimated_minutes": c.estimated_minutes,
            "module_count": len(c.modules),
            "assignment": {
                "status": assignments[c.id].status,
                "progress_percent": assignments[c.id].progress_percent,
                "last_score": assignments[c.id].last_score,
                "deadline": assignments[c.id].deadline.isoformat() if assignments[c.id].deadline else None,
            } if c.id in assignments else None,
        }
        for c in courses
    ]


@app.get("/api/courses/{course_id}")
def get_course(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).options(joinedload(Course.modules).joinedload(Module.questions), joinedload(Course.department)).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "department": course.department.name,
        "skill_level": course.skill_level,
        "estimated_minutes": course.estimated_minutes,
        "modules": [
            {
                "id": m.id,
                "title": m.title,
                "content_type": m.content_type,
                "content_text": m.content_text,
                "question_count": len(m.questions),
            }
            for m in sorted(course.modules, key=lambda item: item.sort_order)
        ],
    }


@app.post("/api/courses", dependencies=[Depends(require_roles("Admin"))])
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"message": "Course created", "id": course.id}


@app.put("/api/courses/{course_id}", dependencies=[Depends(require_roles("Admin"))])
def update_course(course_id: int, payload: CourseCreate, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in payload.model_dump().items():
        setattr(course, key, value)
    db.commit()
    return {"message": "Course updated"}


@app.delete("/api/courses/{course_id}", dependencies=[Depends(require_roles("Admin"))])
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}


@app.post("/api/assignments", dependencies=[Depends(require_roles("Admin", "Manager"))])
def assign_course(payload: AssignmentCreate, db: Session = Depends(get_db)):
    assignment = CourseAssignment(employee_id=payload.employee_id, course_id=payload.course_id, deadline=payload.deadline)
    db.add(assignment)
    db.add(Notification(user_id=payload.employee_id, message=f"New course assigned (Course #{payload.course_id})"))
    db.commit()
    return {"message": "Course assigned"}


@app.get("/api/modules/{module_id}/quiz")
def get_quiz(module_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    module = db.query(Module).options(joinedload(Module.questions)).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    questions = list(module.questions)
    random.shuffle(questions)
    return {
        "module_id": module.id,
        "module_title": module.title,
        "pass_score": PASS_SCORE,
        "questions": [
            {
                "id": q.id,
                "prompt": q.prompt,
                "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
            }
            for q in questions
        ],
    }


@app.post("/api/quiz/submit")
def submit_quiz(payload: QuizSubmission, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    module = db.query(Module).options(joinedload(Module.course), joinedload(Module.questions)).filter(Module.id == payload.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    questions = module.questions
    correct = sum(1 for q in questions if payload.answers.get(q.id) == q.correct_option)
    score = round((correct / len(questions)) * 100, 1) if questions else 0
    attempt = QuizAttempt(employee_id=current_user.id, module_id=module.id, score=score, passed=score >= PASS_SCORE, time_spent_minutes=payload.time_spent_minutes)
    db.add(attempt)
    assignment = db.query(CourseAssignment).filter(CourseAssignment.employee_id == current_user.id, CourseAssignment.course_id == module.course_id).first()
    if assignment:
        assignment.status = "completed" if score >= PASS_SCORE else "in_progress"
        assignment.progress_percent = 100 if score >= PASS_SCORE else max(assignment.progress_percent, 60)
        assignment.last_score = score
        assignment.total_time_spent_minutes += payload.time_spent_minutes
        if not assignment.started_at:
            assignment.started_at = datetime.utcnow()
        if score >= PASS_SCORE:
            assignment.completed_at = datetime.utcnow()
            db.add(BadgeAward(user_id=current_user.id, badge_name=f"{module.course.title} Graduate", points=50))
            db.add(Notification(user_id=current_user.id, message=f"You completed {module.course.title}"))
    db.commit()
    return {"score": score, "passed": score >= PASS_SCORE, "correct_answers": correct, "total_questions": len(questions)}


@app.get("/api/reports/export")
def export_report(current_user: User = Depends(require_roles("Admin", "Manager")), db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee", "Department", "Course", "Status", "Score", "Progress", "Time Spent"])
    rows = (
        db.query(User.full_name, Department.name, Course.title, CourseAssignment.status, CourseAssignment.last_score, CourseAssignment.progress_percent, CourseAssignment.total_time_spent_minutes)
        .join(Department, User.department_id == Department.id)
        .join(CourseAssignment, CourseAssignment.employee_id == User.id)
        .join(Course, Course.id == CourseAssignment.course_id)
        .all()
    )
    for row in rows:
        writer.writerow(row)
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=learning-report.csv"})


@app.get("/api/seed-users")
def seed_users_info():
    return JSONResponse([
        {"role": "Admin", "email": "admin@carencure.com", "password": "Admin@123"},
        {"role": "Manager", "email": "manager@carencure.com", "password": "Manager@123"},
        {"role": "Employee", "email": "sara@carencure.com", "password": "Employee@123"},
    ])
