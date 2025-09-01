from typing import Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from config import settings

oauth2_scheme = HTTPBearer()

def get_jwks_url() -> str:
    return (
        f"https://cognito-idp.{settings.region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )

def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> Dict:
    access_token = token.credentials
    jwks_url = get_jwks_url()

    try:
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(access_token).key

        payload = jwt.decode(
            access_token,
            signing_key,
            algorithms=["RS256"],
            issuer=f"https://cognito-idp.{settings.region}.amazonaws.com/{settings.cognito_user_pool_id}",
            # Para access tokens no se valida "audience" por defecto.
        )

        if payload.get("token_use") != "access":
            raise PyJWTError("Invalid token use. Must be an 'access' token.")

        return payload

    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
