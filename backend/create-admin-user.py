"""
Create an admin (owner) user via CLI prompts.
Usage: python create-admin-user.py
"""
import asyncio
import sys
import getpass

from src.app.services.user_service import UserService
from src.app.schemas.user_schema import UserCreationSchema
from src.db.session import get_async_session


async def main():
    print("═" * 40)
    print("  Riley Estate — Create Admin User")
    print("═" * 40)

    email = input("Email: ").strip()
    username = input("Username: ").strip()
    firstname = input("First name: ").strip()
    lastname = input("Last name: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("❌ Passwords do not match.")
        sys.exit(1)

    user_data = UserCreationSchema(
        email=email,
        username=username,
        password=password,
        confirm_password=confirm,
        firstname=firstname,
        lastname=lastname,
        role="owner",
    )

    service = UserService()

    async with get_async_session() as session:
        existing = await service.user_exists(email, session)
        if existing:
            print(f"❌ User with email '{email}' already exists.")
            sys.exit(1)

        user = await service.create_user(user_data, session)
        print(f"\n✅ Admin user created!")
        print(f"   ID    : {user.id}")
        print(f"   Email : {user.email}")
        print(f"   Role  : {user.role}")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
