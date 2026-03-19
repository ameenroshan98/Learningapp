from datetime import datetime
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CourseCreate(BaseModel):
    title: str
    description: str
    department_id: int
    skill_level: str
    estimated_minutes: int


class AssignmentCreate(BaseModel):
    employee_id: int
    course_id: int
    deadline: datetime | None = None


class QuizSubmission(BaseModel):
    module_id: int
    answers: dict[int, str]
    time_spent_minutes: int = 0
