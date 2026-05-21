from sqlalchemy.orm import Session
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)


async def login(request: LoginRequest, db: Session) -> TokenResponse:
    """유저 로그인 처리"""
    # TODO: 구현
    pass


async def signup(request: SignupRequest, db: Session) -> UserResponse:
    """유저 회원가입 처리"""
    # TODO: 구현
    pass


async def logout(current_user) -> MessageResponse:
    """로그아웃 처리"""
    # TODO: 구현
    pass


async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """토큰 갱신 처리"""
    # TODO: 구현
    pass
