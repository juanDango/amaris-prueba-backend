from typing import Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError # ¡CORRECCIÓN! Importa PyJWTError desde jwt.exceptions
import requests
import json # Necesario para la decodificación manual del encabezado
import base64 # Necesario para la decodificación manual del encabezado
from config import settings


# This will handle getting the token from the header
oauth2_scheme = HTTPBearer()


def get_jwks():
    """
    Consigue la JWKS desde el endpoint de Cognito
    """

    jwks_url = (
        f"https://cognito-idp.{settings.region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        jwks_cache = response.json()["keys"]
        return jwks_cache
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not fetch JWKS: {e}",
        )



def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> Dict:
    """
    Obtiene el usuario actual decodificando y validando el token JWT
    
    Args:
        token (HTTPAuthorizationCredentials): El token JWT extraído del encabezado de autorización.
        
    Returns:
        Dict: El payload decodificado del token JWT."""
    jwks = get_jwks()
    access_token = token.credentials

    try:
        parts = access_token.split('.')
        if len(parts) != 3:
            raise PyJWTError("Invalid JWT token format: expected 3 parts.")

        header_encoded = parts[0]
        padding_needed = len(header_encoded) % 4
        if padding_needed > 0:
            header_encoded += '=' * (4 - padding_needed)

        header_decoded = base64.urlsafe_b64decode(header_encoded).decode('utf-8')
        header = json.loads(header_decoded)
        kid = header.get("kid")

        if not kid:
            raise PyJWTError("Token is missing 'kid' in the header")

        rsa_key = next((key for key in jwks if key["kid"] == kid), None)
        if not rsa_key:
            raise PyJWTError("Could not find a matching public key in JWKS")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key)

        payload = jwt.decode(
            access_token,
            public_key,
            algorithms=["RS256"],
            issuer=f"https://cognito-idp.{settings.region}.amazonaws.com/{settings.cognito_user_pool_id}",
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