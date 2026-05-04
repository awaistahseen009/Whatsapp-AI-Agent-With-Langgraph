from pydantic import BaseModel, Field
from typing import Optional


class UserCreationSchema(BaseModel):
    email: str = Field(max_length=40, description="Email of the user")
    username: str = Field(max_length=30, description="Username of the user")
    password: str = Field(min_length=6, description="Password of the user")
    confirm_password: str = Field(description="Confirm password of the user")
    firstname: str = Field(description="First name of the user")
    lastname: str = Field(description="Last name of the user")
    role: str = Field(default="agent", description="Role: owner or agent")


class UserLoginSchema(BaseModel):
    email: str = Field(description="User email")
    password: str = Field(description="User Password")


class UserLogoutSchema(BaseModel):
    refresh_token: str


class SecurityQuestionSchema(BaseModel):
    question: str = Field(min_length=5)
    answer: str = Field(min_length=2)


class ChangePasswordSchema(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class ForgotPasswordSchema(BaseModel):
    email: str = Field(description="Email of the user requesting password reset")


class VerifySecurityAnswerSchema(BaseModel):
    email: str
    answer: str


class ResetPasswordSchema(BaseModel):
    email: str
    answer: str
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)