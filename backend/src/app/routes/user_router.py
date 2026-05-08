from fastapi import APIRouter, Depends, status, Body
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.schemas.user_schema import (
    UserCreationSchema, UserLoginSchema, UserLogoutSchema,
    SecurityQuestionSchema, ChangePasswordSchema,
    ForgotPasswordSchema, ResetPasswordSchema
)
from src.app.models.user import User
from src.app.services.user_service import UserService
from src.app.dependencies.bearer import AccessTokenBearer, RefreshTokenBearer, RoleChecker
from src.app.utils.utils import generate_hash_password, verify_password, create_access_token, decode_token
from fastapi.exceptions import HTTPException
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse
from src.db.redis import add_token_to_blacklist, get_token_blacklist

service = UserService()
auth_router = APIRouter()

REFRESH_TOKEN_EXPIRY = 2  # In days

# ─── Owner-only: create agent accounts ────────────────────────────────────────

@auth_router.post("/signup/", status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreationSchema,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    email = user_data.email
    user_exists = await service.user_exists(email, session)
    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists with this email. Please login")
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password and confirmed password aren't same")
    new_user: User = await service.create_user(user_data, session)
    return new_user.model_dump()

@auth_router.get("/agents/")
async def get_all_agents(
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session)
):
    from sqlmodel import select
    from src.app.models.user import User
    
    statement = select(User)
    results = await session.exec(statement)
    users = results.all()
    
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "created_at": u.created_at.isoformat()
        } for u in users
    ]


# ─── Login / Logout / Token ──────────────────────────────────────────────────

@auth_router.get("/refresh_token/")
async def get_new_access_token(token_data: dict = Depends(RefreshTokenBearer())):
    if datetime.fromisoformat(token_data['expiry']) > datetime.now():
        return JSONResponse(
            {
                "access_token": create_access_token(
                    user_data=token_data
                )
            }
        )
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please login again")


@auth_router.post("/login/")
async def user_login(
    user_data: UserLoginSchema,
    session: AsyncSession = Depends(get_session)
):
    if user_data.email is None or user_data.password is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Please enter the correct password and email")
        
    user: User = await service.get_user_by_email(user_data.email, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
        
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
        
    access_token = create_access_token(
        user_data={
            'email': user.email,
            "user_id": str(user.id),
            "role": user.role.value
        }
    )
    refresh_token = create_access_token(
        user_data={
            'email': user.email,
            "user_id": str(user.id),
            "role": user.role.value
        },
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
        refresh=True
    )
    return JSONResponse(
        {
            "message": "Login Successful",
            "user": {
                'email': user.email,
                "user_id": str(user.id),
                "role": user.role.value
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    )


@auth_router.post("/logout/")
async def revoke_token(logout_data: UserLogoutSchema = Body(...), token_data: dict = Depends(AccessTokenBearer())):
    refresh_token = decode_token(logout_data.refresh_token)
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a valid refresh token")
    refresh_jti = refresh_token['jti']
    access_jti = token_data['jti']
    await add_token_to_blacklist(jti=access_jti)
    await add_token_to_blacklist(jti=refresh_jti, expiry=timedelta(days=2))
    return JSONResponse({"message": "Logged out successfully"}, status_code=status.HTTP_200_OK)


# ─── Security Question ───────────────────────────────────────────────────────

@auth_router.post("/set-question/")
async def set_question(
    security_schema: SecurityQuestionSchema,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    user_id = token_data.get("user", {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token data")
    sq = await service.set_security_question(
        user_id=user_id,
        question=security_schema.question,
        answer=security_schema.answer,
        session=session
    )
    return {"message": "Security question set successfully", "question_id": str(sq.question_id)}

@auth_router.get("/has-security-question/")
async def has_security_question(
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    from sqlmodel import select
    from src.app.models.security_question import SecurityQuestion
    import uuid
    
    user_id = token_data.get("user", {}).get("user_id")
    if not user_id:
        return {"has_security_question": False}
        
    statement = select(SecurityQuestion).where(SecurityQuestion.user_id == uuid.UUID(user_id))
    result = await session.exec(statement)
    return {"has_security_question": result.first() is not None}

# ─── Change Password ─────────────────────────────────────────────────────────

@auth_router.post("/change-password/")
async def change_password(
    data: ChangePasswordSchema,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirm password don't match")

    user_id = token_data.get("user", {}).get("user_id")
    user = await service.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is incorrect")

    await service.change_password(user_id, data.new_password, session)
    return {"message": "Password changed successfully"}


# ─── Forgot Password Flow ────────────────────────────────────────────────────

@auth_router.post("/forgot-password/")
async def forgot_password(
    data: ForgotPasswordSchema,
    session: AsyncSession = Depends(get_session)
):
    """Step 1: User provides email → returns their security question."""
    user, sq = await service.get_security_question(data.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found with this email")
    if not sq:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No security question set for this account. Please contact support.")
    return {"question": sq.question, "email": data.email}


@auth_router.post("/reset-password/")
async def reset_password(
    data: ResetPasswordSchema,
    session: AsyncSession = Depends(get_session)
):
    """Step 2: User answers security question + provides new password."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirm password don't match")

    is_valid, user = await service.verify_security_answer(data.email, data.answer, session)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect security answer")

    await service.reset_password(data.email, data.new_password, session)
    return {"message": "Password reset successfully. Please login with your new password."}