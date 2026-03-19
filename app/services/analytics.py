from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import BadgeAward, Course, CourseAssignment, Department, User


def employee_dashboard(db: Session, user: User) -> dict:
    assignments = db.query(CourseAssignment).filter(CourseAssignment.employee_id == user.id).all()
    return {
        "courses_started": sum(1 for a in assignments if a.status in {"in_progress", "completed"}),
        "courses_completed": sum(1 for a in assignments if a.status == "completed"),
        "avg_score": round(sum(a.last_score for a in assignments) / len(assignments), 1) if assignments else 0,
        "time_spent": sum(a.total_time_spent_minutes for a in assignments),
        "leaderboard_points": sum(b.points for b in user.badges),
    }


def manager_dashboard(db: Session, manager: User) -> dict:
    team_ids = [u.id for u in db.query(User).filter(User.manager_id == manager.id).all()]
    team_assignments = db.query(CourseAssignment).filter(CourseAssignment.employee_id.in_(team_ids)).all() if team_ids else []
    return {
        "team_size": len(team_ids),
        "completion_rate": round((sum(1 for a in team_assignments if a.status == "completed") / len(team_assignments)) * 100, 1) if team_assignments else 0,
        "average_score": round(sum(a.last_score for a in team_assignments) / len(team_assignments), 1) if team_assignments else 0,
        "overdue_courses": sum(1 for a in team_assignments if a.deadline and a.status != "completed"),
    }


def admin_dashboard(db: Session) -> dict:
    total_assignments = db.query(func.count(CourseAssignment.id)).scalar() or 0
    completed_assignments = db.query(func.count(CourseAssignment.id)).filter(CourseAssignment.status == "completed").scalar() or 0
    top_performers = (
        db.query(User.full_name, Department.name, func.sum(BadgeAward.points).label("points"))
        .join(Department, User.department_id == Department.id)
        .join(BadgeAward, BadgeAward.user_id == User.id)
        .group_by(User.id, Department.name)
        .order_by(func.sum(BadgeAward.points).desc())
        .limit(5)
        .all()
    )
    low_performers = (
        db.query(User.full_name, Department.name, func.avg(CourseAssignment.last_score).label("avg_score"))
        .join(Department, User.department_id == Department.id)
        .join(CourseAssignment, CourseAssignment.employee_id == User.id)
        .group_by(User.id, Department.name)
        .order_by(func.avg(CourseAssignment.last_score).asc())
        .limit(5)
        .all()
    )
    department_completion = (
        db.query(
            Department.name,
            func.sum(case((CourseAssignment.status == "completed", 1), else_=0)).label("completed"),
            func.count(CourseAssignment.id).label("total"),
        )
        .join(Course, Course.department_id == Department.id)
        .join(CourseAssignment, CourseAssignment.course_id == Course.id)
        .group_by(Department.name)
        .all()
    )
    return {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "total_courses": db.query(func.count(Course.id)).scalar() or 0,
        "completion_rate": round((completed_assignments / total_assignments) * 100, 1) if total_assignments else 0,
        "top_performers": [dict(name=n, department=d, points=p) for n, d, p in top_performers],
        "low_performers": [dict(name=n, department=d, avg_score=round(s or 0, 1)) for n, d, s in low_performers],
        "department_completion": [dict(department=n, completion_rate=round((c / t) * 100, 1) if t else 0) for n, c, t in department_completion],
    }
