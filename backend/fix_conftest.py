# Fix for conftest.py SQLite dialect issue

# Replace line 49 in conftest.py with:
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Actually, let's use the correct async SQLite dialect:
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# If that doesn't work, try:
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Or use standard SQLite with sync engine:
TEST_DATABASE_URL = "sqlite:///:memory:"

# And change create_async_engine to create_engine for sync SQLite
# But let's try the proper async dialect first
