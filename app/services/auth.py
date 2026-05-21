from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.account import Account, PbUser
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    verify_token,
)
from datetime import date


def check_password(plain: str, stored: str) -> bool:
    """평문 패스워드 매칭과 암호화 해시 매칭을 둘 다 지원"""
    if plain == stored:
        return True
    try:
        return verify_password(plain, stored)
    except Exception:
        return False


async def login(request: LoginRequest, db: Session) -> TokenResponse:
    """유저 로그인 처리"""
    account = db.query(Account).filter(Account.id == request.u_id).first()
    if not account or not check_password(request.password, account.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="아이디 또는 비밀번호가 일치하지 않습니다.",
        )

    # 토큰 페이로드 구성
    token_data = {"sub": account.id, "role": account.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def signup(request: SignupRequest, db: Session) -> UserResponse:
    """유저 회원가입 처리"""
    # 아이디 중복 체크
    existing_account = db.query(Account).filter(Account.id == request.u_id).first()
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 아이디입니다.",
        )

    # 이메일 중복 체크
    existing_pb = db.query(PbUser).filter(PbUser.email == request.email).first()
    if existing_pb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다.",
        )

    # 계정 생성 (암호화하여 저장)
    new_account = Account(
        id=request.u_id,
        password=hash_password(request.password),
        role="user",
    )
    db.add(new_account)
    db.flush()

    # 기본 PB User 프로필 생성 (임시 데이터)
    new_pb = PbUser(
        u_id=request.u_id,
        name=request.name,
        email=request.email,
        number="010-0000-0000",
        branch=1,  # 임시 기본 지점 ID
        status="재직",
        position="PB",
        start_date=date.today(),
        birth_date=date(1990, 1, 1),
    )
    db.add(new_pb)
    db.commit()
    db.refresh(new_account)

    return UserResponse(
        u_id=new_account.id,
        name=new_pb.name,
        email=new_pb.email,
        role=new_account.role,
    )


async def logout(current_user) -> MessageResponse:
    """로그아웃 처리"""
    # JWT 방식이므로 클라이언트측 토큰 파기로 처리, 서버측은 성공 메시지 반환
    return MessageResponse(message="성공적으로 로그아웃되었습니다.")


async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """토큰 갱신 처리"""
    payload = verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 리프레시 토큰입니다.",
        )

    u_id = payload.get("sub")
    role = payload.get("role")

    token_data = {"sub": u_id, "role": role}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )

