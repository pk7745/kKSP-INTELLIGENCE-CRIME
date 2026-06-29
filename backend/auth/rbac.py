import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
try:
    from jose import JWTError, jwt as _jose_jwt
    def _encode(payload, secret, algorithm):
        return _jose_jwt.encode(payload, secret, algorithm=algorithm)
    def _decode(token, secret, algorithms):
        return _jose_jwt.decode(token, secret, algorithms=algorithms)
    _JWTError = JWTError
except Exception:
    import jwt as _pyjwt
    def _encode(payload, secret, algorithm):
        return _pyjwt.encode(payload, secret, algorithm=algorithm)
    def _decode(token, secret, algorithms):
        return _pyjwt.decode(token, secret, algorithms=algorithms)
    _JWTError = _pyjwt.PyJWTError
from pydantic import BaseModel

logger = logging.getLogger("kaveri.auth")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-kaveri-ksp-2025")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Demo users: {username: {password, role, district, name}}
DEMO_USERS = {
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "district": None,
        "name": "KAVERI Administrator",
        "employee_id": "ADMIN001",
    },
    "analyst": {
        "password": "analyst123",
        "role": "Analyst",
        "district": None,
        "name": "Senior Crime Analyst",
        "employee_id": "ANA001",
    },
    "officer": {
        "password": "officer123",
        "role": "Officer",
        "district": "BEU",
        "name": "Inspector Rajesh Kumar",
        "employee_id": "OFF001",
    },
    "viewer": {
        "password": "viewer123",
        "role": "Viewer",
        "district": "BEU",
        "name": "Sub-Inspector Priya Sharma",
        "employee_id": "VIEW001",
    },
}

# Role permissions matrix
ROLE_PERMISSIONS = {
    "Admin": ["read", "write", "delete", "export", "manage_users", "view_all_districts"],
    "Analyst": ["read", "write", "export", "view_all_districts"],
    "Officer": ["read", "export"],
    "Viewer": ["read"],
}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    district: Optional[str]
    name: str
    permissions: list


class UserInfo(BaseModel):
    username: str
    name: str
    role: str
    district: Optional[str]
    employee_id: str
    permissions: list


def create_token(username: str, user_data: dict) -> str:
    payload = {
        "sub": username,
        "role": user_data["role"],
        "district": user_data["district"],
        "name": user_data["name"],
        "employee_id": user_data["employee_id"],
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return _encode(payload, JWT_SECRET, ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = _decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except _JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )
    role = payload.get("role", "Viewer")
    return {
        "username": username,
        "name": payload.get("name", username),
        "role": role,
        "district": payload.get("district"),
        "employee_id": payload.get("employee_id", ""),
        "permissions": ROLE_PERMISSIONS.get(role, []),
    }


def require_permission(permission: str):
    async def checker(user: dict = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required. Your role: {user['role']}",
            )
        return user
    return checker


def filter_district(user: dict, district_id: Optional[str]) -> Optional[str]:
    """If Officer or Viewer, enforce district scope. Admin/Analyst see all."""
    if user["role"] in ("Officer", "Viewer"):
        return user.get("district") or district_id
    return district_id


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username.lower().strip()
    user = DEMO_USERS.get(username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_token(username, user)
    logger.info(f"Login: {username} ({user['role']})")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        district=user["district"],
        name=user["name"],
        permissions=ROLE_PERMISSIONS.get(user["role"], []),
    )


@router.post("/login/json", response_model=TokenResponse)
async def login_json(req: LoginRequest):
    username = req.username.lower().strip()
    user = DEMO_USERS.get(username)
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_token(username, user)
    logger.info(f"Login: {username} ({user['role']})")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        district=user["district"],
        name=user["name"],
        permissions=ROLE_PERMISSIONS.get(user["role"], []),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(user: dict = Depends(get_current_user)):
    return UserInfo(
        username=user["username"],
        name=user["name"],
        role=user["role"],
        district=user["district"],
        employee_id=user["employee_id"],
        permissions=user["permissions"],
    )
