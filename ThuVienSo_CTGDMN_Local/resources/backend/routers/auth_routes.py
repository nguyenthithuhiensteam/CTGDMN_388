from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from backend import db
from backend.audit import write_audit_log
from backend.auth import CurrentUser, create_token, get_current_user, hash_password, require_admin, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterSchoolRequest(BaseModel):
    school_name: str
    city: str = ""
    admin_email: str
    admin_password: str
    admin_full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateTeacherRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class AuthResponse(BaseModel):
    token: str
    role: str
    school_id: int
    school_name: str
    full_name: str


def _login_response(conn, user_row) -> AuthResponse:
    school = conn.execute(db.schools.select().filter_by(id=user_row["school_id"])).mappings().fetchone()
    token = create_token(user_row["id"], user_row["school_id"], user_row["role"])
    return AuthResponse(
        token=token,
        role=user_row["role"],
        school_id=user_row["school_id"],
        school_name=school["name"] if school else "",
        full_name=user_row["full_name"] or "",
    )


@router.post("/register-school", response_model=AuthResponse)
def register_school(payload: RegisterSchoolRequest) -> AuthResponse:
    if not payload.school_name.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập tên trường.")
    if not payload.admin_email.strip() or len(payload.admin_password) < 6:
        raise HTTPException(status_code=400, detail="Email hợp lệ và mật khẩu tối thiểu 6 ký tự.")
    with db.get_connection() as conn:
        with conn.begin():
            try:
                school_id = db.insert_returning_id(
                    conn, db.schools, {"name": payload.school_name.strip(), "city": payload.city.strip()}
                )
                user_id = db.insert_returning_id(
                    conn,
                    db.users,
                    {
                        "school_id": school_id,
                        "email": payload.admin_email.strip().lower(),
                        "password_hash": hash_password(payload.admin_password),
                        "full_name": payload.admin_full_name.strip(),
                        "role": "admin",
                    },
                )
            except IntegrityError:
                raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
            write_audit_log(conn, school_id, user_id, "create", "school", school_id, payload.school_name.strip())
            user_row = conn.execute(db.users.select().filter_by(id=user_id)).mappings().fetchone()
            return _login_response(conn, user_row)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    with db.get_connection() as conn:
        user_row = conn.execute(
            db.users.select().filter_by(email=payload.email.strip().lower())
        ).mappings().fetchone()
        if not user_row or not verify_password(payload.password, user_row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
        return _login_response(conn, user_row)


@router.get("/me")
def auth_me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        user_row = conn.execute(db.users.select().filter_by(id=current_user.user_id)).mappings().fetchone()
        school = conn.execute(db.schools.select().filter_by(id=current_user.school_id)).mappings().fetchone()
        return {
            "user_id": current_user.user_id,
            "email": user_row["email"] if user_row else "",
            "full_name": user_row["full_name"] if user_row else "",
            "role": current_user.role,
            "school_id": current_user.school_id,
            "school_name": school["name"] if school else "",
        }


@router.post("/teachers")
def create_teacher(
    payload: CreateTeacherRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    require_admin(current_user)
    if not payload.email.strip() or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Email hợp lệ và mật khẩu tối thiểu 6 ký tự.")
    with db.get_connection() as conn:
        with conn.begin():
            try:
                user_id = db.insert_returning_id(
                    conn,
                    db.users,
                    {
                        "school_id": current_user.school_id,
                        "email": payload.email.strip().lower(),
                        "password_hash": hash_password(payload.password),
                        "full_name": payload.full_name.strip(),
                        "role": "teacher",
                    },
                )
            except IntegrityError:
                raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "teacher", user_id, payload.email
            )
    return {"status": "ok", "user_id": user_id}


@router.get("/teachers")
def list_teachers(current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    require_admin(current_user)
    with db.get_connection() as conn:
        result = conn.execute(
            db.users.select().filter_by(school_id=current_user.school_id).order_by(db.users.c.created_at)
        )
        return [{k: v for k, v in row.items() if k != "password_hash"} for row in db.rows_as_dicts(result)]
