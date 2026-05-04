from src.app.models.user import User
from src.app.models.security_question import SecurityQuestion
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.schemas.user_schema import UserCreationSchema
from src.app.utils.utils import generate_hash_password, verify_password


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()

    async def get_user_by_id(self, user_id: str, session: AsyncSession):
        statement = select(User).where(User.id == user_id)
        result = await session.exec(statement)
        return result.first()

    async def user_exists(self, email: str, session: AsyncSession):
        return True if await self.get_user_by_email(email, session) is not None else False

    async def create_user(self, user_data: UserCreationSchema, session: AsyncSession):
        user_data_dict = user_data.model_dump()
        password = user_data.password
        user_data_dict.pop("password")
        user_data_dict.pop("confirm_password")
        user_data_dict["name"] = f"{user_data_dict.pop('firstname')} {user_data_dict.pop('lastname')}"
        user_data_dict.pop("username", None)
        new_user = User(**user_data_dict)
        new_user.password_hash = generate_hash_password(password)
        session.add(new_user)
        await session.commit()
        return new_user

    # ─── Security Questions ───────────────────────────────────────────────

    async def set_security_question(self, user_id: str, question: str, answer: str, session: AsyncSession):
        answer_hash = generate_hash_password(answer.strip().lower())
        sq = SecurityQuestion(user_id=user_id, question=question, answer_hash=answer_hash)
        session.add(sq)
        await session.commit()
        return sq

    async def get_security_question(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        if not user:
            return None, None
        statement = select(SecurityQuestion).where(SecurityQuestion.user_id == user.id)
        result = await session.exec(statement)
        sq = result.first()
        return user, sq

    async def verify_security_answer(self, email: str, answer: str, session: AsyncSession):
        user, sq = await self.get_security_question(email, session)
        if not user or not sq:
            return False, None
        is_valid = verify_password(answer.strip().lower(), sq.answer_hash)
        return is_valid, user

    # ─── Password Management ─────────────────────────────────────────────

    async def change_password(self, user_id: str, new_password: str, session: AsyncSession):
        user = await self.get_user_by_id(user_id, session)
        if not user:
            return None
        user.password_hash = generate_hash_password(new_password)
        session.add(user)
        await session.commit()
        return user

    async def reset_password(self, email: str, new_password: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        if not user:
            return None
        user.password_hash = generate_hash_password(new_password)
        session.add(user)
        await session.commit()
        return user