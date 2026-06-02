from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import verify_token
from app.models.account import Account

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """JWT 토큰에서 현재 사용자 정보를 추출하여 반환"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(Account).filter(Account.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_admin(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """현재 사용자가 관리자인지 확인"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return current_user


def get_current_branch_manager(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """현재 사용자가 지점장(pb_user.position == '지점장')이거나 관리자인지 확인"""
    is_branch_manager = (
        current_user.pb_user is not None and 
        current_user.pb_user.position == "지점장"
    )
    is_admin = current_user.role == "admin"
    
    if not (is_admin or is_branch_manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="지점장 또는 관리자 권한이 필요합니다.",
        )
    return current_user
