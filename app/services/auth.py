from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.account import Account, PbUser
from app.models.branch import Branch
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
from datetime import date, datetime


def check_password(plain: str, stored: str) -> bool:
    """평문 패스워드 매칭과 암호화 해시 매칭을 둘 다 지원"""
    if plain == stored:
        return True
    try:
        return verify_password(plain, stored)
    except Exception:
        return False


def login(request: LoginRequest, db: Session) -> TokenResponse:
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

    # PB 유저의 이름 조회
    user_name = "PB직원"
    if account.role in ("admin", "superadmin"):
        pb_user = account.pb_user
        if pb_user:
            user_name = pb_user.name
        else:
            user_name = "관리자"
    else:
        pb_user = account.pb_user
        if pb_user:
            user_name = pb_user.name

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        name=user_name,
    )


def signup(request: SignupRequest, db: Session) -> UserResponse:
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

    # 지점 정보 조회
    branch_record = db.query(Branch).filter(Branch.name == request.branch).first()
    if not branch_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="존재하지 않는 지점입니다.",
        )

    # 생년월일 파싱 (예: 2002.05.04 또는 2002-05-04)
    try:
        clean_date = request.birth_date.replace(".", "-")
        birth_date_parsed = datetime.strptime(clean_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="생년월일 형식이 올바르지 않습니다. (예: 2002.05.04)",
        )

    # 입사일 파싱 (예: 2026.05.22 또는 2026-05-22)
    try:
        clean_start_date = request.start_date.replace(".", "-")
        start_date_parsed = datetime.strptime(clean_start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="입사일 형식이 올바르지 않습니다. (예: 2026.05.22)",
        )

    # 계정 생성 (암호화하여 저장, 역할은 user)
    new_account = Account(
        id=request.u_id,
        password=hash_password(request.password),
        role="user",
    )
    db.add(new_account)
    db.flush()

    # PB User 프로필 생성 및 컬럼 값 지정
    new_pb = PbUser(
        u_id=request.u_id,
        name=request.name,
        email=request.email,
        number=request.number,
        branch=branch_record.b_id,
        status="재직",
        position="PB",
        start_date=start_date_parsed,
        birth_date=birth_date_parsed,
    )
    db.add(new_pb)
    db.commit()
    db.refresh(new_account)

    return UserResponse(
        u_id=new_account.id,
        name=new_pb.name,
        email=new_pb.email,
        role=new_account.role,
        position=new_pb.position,
    )


def logout(current_user) -> MessageResponse:
    """로그아웃 처리"""
    # JWT 방식이므로 클라이언트측 토큰 파기로 처리, 서버측은 성공 메시지 반환
    return MessageResponse(message="성공적으로 로그아웃되었습니다.")


def refresh_token(request: RefreshRequest) -> TokenResponse:
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


def get_me(current_user, db: Session) -> UserResponse:
    """현재 로그인한 유저의 최신 정보 조회"""
    user_name = "PB직원"
    email = ""
    branch_name = None
    position_name = None
    if current_user.role in ("admin", "superadmin"):
        pb_user = current_user.pb_user
        if pb_user:
            user_name = pb_user.name
            email = pb_user.email
            position_name = pb_user.position
            if pb_user.branch_rel:
                branch_name = pb_user.branch_rel.name
        else:
            user_name = "관리자"
            email = "admin@poom.com"
            position_name = "관리자"
    else:
        pb_user = current_user.pb_user
        if pb_user:
            user_name = pb_user.name
            email = pb_user.email
            position_name = pb_user.position
            if pb_user.branch_rel:
                branch_name = pb_user.branch_rel.name

    return UserResponse(
        u_id=current_user.id,
        name=user_name,
        email=email,
        role=current_user.role,
        branch=branch_name,
        position=position_name,
    )


