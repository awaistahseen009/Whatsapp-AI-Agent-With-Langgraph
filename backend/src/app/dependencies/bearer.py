from fastapi.security import HTTPBearer
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi import status, Depends
from src.app.utils.utils import decode_token
from src.db.redis import get_token_blacklist

class TokenBearer(HTTPBearer):
    def __init__(self,auto_error:bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request:Request):
        creds =  await super().__call__(request)
        token = creds.credentials
        token_data = decode_token(token)
        if not self.validate_token(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token")
        
        if await get_token_blacklist(token_data['jti']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
                "error": "Invalid or revoked token",
                "resolution": "Please login again and get a new token"
            })

        self.verify_token_data(token_data)

        return token_data

    def validate_token(self, token:str):
        token_data = decode_token(token)
        return True if token_data is not None else False
    
    def verify_token_data(self, token_data:dict):
        raise NotImplementedError("Please Override this method in child classes")

class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data:dict):
        if token_data and token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Please provide an access token"
            )
        

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data:dict):
        if token_data and not token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Please provide a refresh token"
            ) 


class RoleChecker:
    """
    Dependency that checks if the authenticated user has one of the allowed roles.
    Usage: Depends(RoleChecker(["owner"]))
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: dict = Depends(AccessTokenBearer())):
        user_role = token_data.get("user", {}).get("role", "agent")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return token_data