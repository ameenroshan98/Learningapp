from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .auth import hash_password
from .models import BadgeAward, Course, CourseAssignment, Department, Module, Notification, Question, User


def seed_data(db: Session) -> None:
    if db.query(Department).count() > 0:
        return
    departments = [
        Department(name="Pharmacy", description="Clinical and retail pharmacy operations"),
        Department(name="FMCG", description="Fast-moving consumer goods teams"),
        Department(name="Sales", description="Field and inside sales teams"),
        Department(name="Operations", description="Supply chain and operations excellence"),
    ]
    db.add_all(departments)
    db.flush()
    admin = User(employee_id="CNC-0001", full_name="Aisha Rahman", email="admin@carencure.com", password_hash=hash_password("Admin@123"), role="Admin", department_id=departments[3].id)
    manager = User(employee_id="CNC-0100", full_name="Omar Hasan", email="manager@carencure.com", password_hash=hash_password("Manager@123"), role="Manager", department_id=departments[2].id)
    employee1 = User(employee_id="CNC-1001", full_name="Sara Ali", email="sara@carencure.com", password_hash=hash_password("Employee@123"), role="Employee", department_id=departments[0].id, manager=manager)
    employee2 = User(employee_id="CNC-1002", full_name="Nabil Ahmed", email="nabil@carencure.com", password_hash=hash_password("Employee@123"), role="Employee", department_id=departments[2].id, manager=manager)
    employee3 = User(employee_id="CNC-1003", full_name="Farhana Noor", email="farhana@carencure.com", password_hash=hash_password("Employee@123"), role="Employee", department_id=departments[1].id, manager=manager)
    db.add_all([admin, manager, employee1, employee2, employee3])
    db.flush()
    courses = [
        Course(title="Pharmacy Compliance Fundamentals", description="Medication safety, storage, and dispensing best practices.", department_id=departments[0].id, skill_level="Beginner", estimated_minutes=45),
        Course(title="High-Impact FMCG Merchandising", description="Improve shelf execution and retail visibility.", department_id=departments[1].id, skill_level="Intermediate", estimated_minutes=35),
        Course(title="Consultative Selling Excellence", description="Build stronger sales conversations and closing skills.", department_id=departments[2].id, skill_level="Intermediate", estimated_minutes=50),
        Course(title="Operations KPI Mastery", description="Use operational dashboards and SOPs effectively.", department_id=departments[3].id, skill_level="Advanced", estimated_minutes=40),
    ]
    db.add_all(courses)
    db.flush()
    modules = [
        Module(course_id=courses[0].id, title="Safe Dispensing Workflow", content_type="text", content_text="Review the 5 rights of medication dispensing and escalation procedures.", sort_order=1),
        Module(course_id=courses[1].id, title="Shelf Execution Checklist", content_type="text", content_text="Learn category placement, pricing checks, and promo compliance.", sort_order=1),
        Module(course_id=courses[2].id, title="Needs Discovery", content_type="text", content_text="Use open-ended questions to understand customer pain points.", sort_order=1),
        Module(course_id=courses[3].id, title="Daily KPI Review", content_type="text", content_text="Track fulfillment, wastage, and service levels every day.", sort_order=1),
    ]
    db.add_all(modules)
    db.flush()
    db.add_all([
        Question(module_id=modules[0].id, prompt="Which step reduces dispensing errors most directly?", option_a="Double-check patient, drug, dose", option_b="Skip verbal confirmation", option_c="Only review expiry dates", option_d="Rely on memory", correct_option="A"),
        Question(module_id=modules[1].id, prompt="What should merchandisers verify daily?", option_a="Shelf cleanliness only", option_b="Planogram and pricing", option_c="Only stockroom count", option_d="Store music volume", correct_option="B"),
        Question(module_id=modules[2].id, prompt="Consultative selling starts with:", option_a="Immediate discounting", option_b="Feature dumping", option_c="Discovery questions", option_d="Closing immediately", correct_option="C"),
        Question(module_id=modules[3].id, prompt="A core operations KPI is:", option_a="Website theme color", option_b="Warehouse accuracy", option_c="Office seating", option_d="Printer toner usage", correct_option="B"),
    ])
    db.add_all([
        CourseAssignment(employee_id=employee1.id, course_id=courses[0].id, status="in_progress", progress_percent=50, total_time_spent_minutes=20, last_score=80, started_at=datetime.utcnow(), deadline=datetime.utcnow() + timedelta(days=7)),
        CourseAssignment(employee_id=employee2.id, course_id=courses[2].id, status="completed", progress_percent=100, total_time_spent_minutes=54, last_score=92, started_at=datetime.utcnow() - timedelta(days=5), completed_at=datetime.utcnow() - timedelta(days=1), deadline=datetime.utcnow() + timedelta(days=2)),
        CourseAssignment(employee_id=employee3.id, course_id=courses[1].id, status="assigned", progress_percent=0, total_time_spent_minutes=0, last_score=0, deadline=datetime.utcnow() + timedelta(days=10)),
    ])
    db.add_all([
        Notification(user_id=employee1.id, message="Course assigned: Pharmacy Compliance Fundamentals", notification_type="in_app"),
        Notification(user_id=employee2.id, message="Congratulations on completing Consultative Selling Excellence", notification_type="in_app"),
        Notification(user_id=manager.id, message="Your team has 1 course nearing deadline", notification_type="in_app"),
    ])
    db.add_all([
        BadgeAward(user_id=employee2.id, badge_name="Sales Champion", points=120),
        BadgeAward(user_id=employee1.id, badge_name="Compliance Starter", points=80),
        BadgeAward(user_id=employee3.id, badge_name="FMCG Explorer", points=40),
    ])
    db.commit()
