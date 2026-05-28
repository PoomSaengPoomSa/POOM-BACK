from pydantic import BaseModel, ConfigDict, Field


# 로그인 요청
class LoginRequest(BaseModel):
    u_id: str
    password: str


# 회원가입 요청
class SignupRequest(BaseModel):
    u_id: str = Field(alias="id")  # 프론트엔드 사번(id) 매핑
    password: str
    name: str
    email: str
    birth_date: str = Field(alias="birthDate")  # 프론트엔드 birthDate(YYYY.MM.DD) 매핑
    region: str
    branch: str  # 지점명 (예: "종로금융센터")
    number: str  # 전화번호
    start_date: str = Field(alias="startDate")  # 프론트엔드 startDate(YYYY.MM.DD) 매핑

    model_config = ConfigDict(populate_by_name=True)


# 토큰 갱신 요청
class RefreshRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


# 토큰 응답
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    name: str | None = None


# 유저 정보 응답
class UserResponse(BaseModel):
    u_id: str
    name: str
    email: str
    role: str
    branch: str | None = None
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
