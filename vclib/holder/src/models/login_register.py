from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(LoginRequest):
    confirm: str


class UserAuthenticationResponse(BaseModel):
    username: str
    access_token: str
    token_type: str = Field(default="Bearer")
