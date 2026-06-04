from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.dependencies import get_current_user
from app.services import auth as auth_service

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """유저 로그인"""
    return auth_service.login(request, db)


@router.post("/signup", response_model=UserResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """유저 회원가입"""
    return auth_service.signup(request, db)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user=Depends(get_current_user)):
    """관리자 및 유저 로그아웃"""
    return auth_service.logout(current_user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest):
    """만료된 Access Token을 Refresh Token을 이용해 재발급"""
    return auth_service.refresh_token(request)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 로그인한 유저 정보 조회"""
    return auth_service.get_me(current_user, db)

