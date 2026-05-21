from pydantic import BaseModel, ConfigDict, Field


# 로그인 요청
class LoginRequest(BaseModel):
    u_id: str
    password: str


# 회원가입 요청
class SignupRequest(BaseModel):
    name: str
    email: str
    u_id: str
    password: str


# 토큰 갱신 요청
class RefreshRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


# 토큰 응답
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 유저 정보 응답
class UserResponse(BaseModel):
    u_id: str
    name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
