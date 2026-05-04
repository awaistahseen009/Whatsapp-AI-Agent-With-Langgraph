from redis.asyncio import StrictRedis
from config import Config
from datetime import timedelta, datetime

TOKEN_EXPIRY = 3600
WHATSAPP_MESSAGE_TTL = 60 * 60 * 24

token_blacklist_client = StrictRedis(
    host = Config.REDIS_HOST, 
    port=Config.REDIS_PORT,
    db=0
)

async def add_token_to_blacklist(jti:str, expiry:timedelta = None):
    await token_blacklist_client.set(
        name=jti, value="", ex = expiry if expiry is not None else timedelta(seconds=TOKEN_EXPIRY)
    )

async def get_token_blacklist(jti:str):
    jti = await token_blacklist_client.get(jti)
    return jti is not None


async def mark_whatsapp_message_seen(message_id: str) -> bool:
    """Return True only the first time a WhatsApp message id is seen."""
    if not message_id:
        return True
    key = f"whatsapp:message:{message_id}"
    return bool(await token_blacklist_client.set(key, "1", ex=WHATSAPP_MESSAGE_TTL, nx=True))

