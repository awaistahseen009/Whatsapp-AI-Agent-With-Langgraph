import asyncio
from sqlalchemy import text
from src.db.session import async_engine

async def check_prices():
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT property_id, price FROM property LIMIT 10"))
        rows = result.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    asyncio.run(check_prices())
