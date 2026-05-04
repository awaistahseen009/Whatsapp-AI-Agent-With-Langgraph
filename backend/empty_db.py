import asyncio
from sqlalchemy import text
from src.db.session import async_engine

async def empty_tables():
    """
    Clears all rows from all tables in the public schema using TRUNCATE CASCADE.
    This preserves the schema structure but effectively resets the database.
    """
    try:
        async with async_engine.begin() as conn:
            # Get all table names in public schema
            result = await conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("No tables found in public schema.")
                return

            print(f"Found {len(tables)} tables to empty: {', '.join(tables)}")

            # TRUNCATE CASCADE cleanly deletes all rows and resets identity cascades
            quoted_tables = [f'"{t}"' for t in tables]
            truncate_query = f"TRUNCATE TABLE {', '.join(quoted_tables)} CASCADE;"
            await conn.execute(text(truncate_query))
            
            print("Successfully emptied all tables!")
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    print("Warning: Empting database in 3 seconds. Press Ctrl+C to abort...")
    import time
    time.sleep(3)
    asyncio.run(empty_tables())
