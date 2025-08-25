from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer
import boto3, hmac, hashlib, base64
from botocore.exceptions import ClientError
from config import settings
from schema.auth import (
    SignupIn, ConfirmIn, LoginIn
)
from repositories.users import create_user


router = APIRouter(prefix="/auth", tags=["auth"])
cog = boto3.client("cognito-idp", region_name=settings.region)
resp = cog.list_user_pools(MaxResults=10)

oauth2scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_secret_hash(username, app_client_id, app_client_secret):
    """
    Calculates the SECRET_HASH required for Cognito API calls.
    """
    message = username + app_client_id
    digest = hmac.new(
        app_client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode()

@router.post("/signup")
async def signup(signup_in: SignupIn):
    """Sign up a new user in Cognito.
    
    Args:
        signup_in (SignupIn): Input data for signing up a user.

    Returns:
        dict: A message indicating the result of the sign-up operation.
    """
    try:
        secret_hash = get_secret_hash(
            signup_in.email,
            settings.cognito_client_id,
            settings.cognito_client_secret
        )

        response = cog.sign_up(
            ClientId=settings.cognito_client_id,
            Username=signup_in.email,
            Password=signup_in.password,
            SecretHash=secret_hash,
        )

        cognito_user_id = response['UserSub']

        user = create_user(signup_in.email, signup_in.phone_number, cognito_user_id)

        return {"message": "User signed up successfully", "user": user, "response": response}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])
    
@router.post("/confirm")
async def confirm(confirm_in: ConfirmIn):
    """Confirm a user's sign-up in Cognito.

    Args:
        confirm_in (ConfirmIn): Input data for confirming a user.

    Returns:
        dict: A message indicating the result of the confirmation operation.
    """
    try:
        secret_hash = get_secret_hash(
            confirm_in.email,
            settings.cognito_client_id,
            settings.cognito_client_secret
        )
        response = cog.confirm_sign_up(
            ClientId=settings.cognito_client_id,
            Username=confirm_in.email,
            ConfirmationCode=confirm_in.confirmation_code,
            SecretHash=secret_hash,
        )
        return {"message": "User confirmed successfully", "response": response}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])
    
@router.post("/login")
async def login(login_in: LoginIn):
    """Log in a user to Cognito and return access and refresh tokens.
    
    Args:
        login_in (LoginIn): Input data for logging in a user.

    Returns:
        dict: A dictionary containing the access token, refresh token, and token type.
    """
    try:
        secret_hash = get_secret_hash(
            login_in.email,
            settings.cognito_client_id,
            settings.cognito_client_secret
        )
        response = cog.initiate_auth(
            ClientId=settings.cognito_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": login_in.email,
                "PASSWORD": login_in.password,
                "SECRET_HASH": secret_hash
            },
        )
        return {
            "access_token": response['AuthenticationResult']['AccessToken'],
            "refresh_token": response['AuthenticationResult']['RefreshToken'],
            "token_type": "Bearer",
        }
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])