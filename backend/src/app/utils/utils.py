from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import uuid
from config import Config
import logging

ACCESS_TOKEN_EXPIRY_TIME = 3600
passwd_context = CryptContext(
    schemes=['bcrypt'],
    bcrypt__truncate_error=False,
)

def generate_hash_password(password: str):
    return passwd_context.hash(password[:72])

def verify_password(password: str, hash: str):
    return passwd_context.verify(password[:72], hash)

def create_access_token(user_data:dict, expiry:timedelta = None, refresh:bool = False):
    payload = {}
    payload['user'] = user_data
    payload['expiry'] = (datetime.now() + (expiry if expiry is not None else timedelta(ACCESS_TOKEN_EXPIRY_TIME))).isoformat()
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = refresh

    token = jwt.encode(
        payload=payload, 
        key= Config.JWT_KEY, 
        algorithm= Config.JWT_ALGORITHM
    )
    return token

def decode_token(token:str):
    try:
        token_data = jwt.decode(
            jwt=token  ,
            key=Config.JWT_KEY, 
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None