from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from backend.core.supabase import supabase_wrapper

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")


class LoginResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user ID.")
    email: str = Field(..., description="Supabase user email.")
    full_name: str = Field(..., description="User metadata full name.")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="New account email.")
    password: str = Field(..., description="New account password.")


class RegisterResponse(BaseModel):
    message: str = Field(..., description="Status feedback message.")


class OAuthRequest(BaseModel):
    provider: str = Field("google", description="OAuth provider name.")


class OAuthResponse(BaseModel):
    url: str | None = Field(None, description="Redirect URL for OAuth.")
    user_id: str | None = Field(None, description="Supabase user ID.")
    email: str | None = Field(None, description="Supabase user email.")
    full_name: str | None = Field(None, description="User full name.")


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest) -> LoginResponse:
    logger.info(f"[Auth API] Login attempt for: {payload.email}")
    if supabase_wrapper.is_mock:
        return LoginResponse(
            user_id="mock-user-123",
            email=payload.email,
            full_name=payload.email.split("@")[0].capitalize(),
        )
    try:
        res = supabase_wrapper.get_client().auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
        user_metadata = getattr(res.user, "user_metadata", {}) or {}
        full_name = user_metadata.get("full_name", payload.email.split("@")[0].capitalize())
        return LoginResponse(user_id=res.user.id, email=res.user.email, full_name=full_name)
    except Exception as e:
        logger.error(f"[Auth API] Login failed for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> RegisterResponse:
    logger.info(f"[Auth API] Registration attempt for: {payload.email}")
    if supabase_wrapper.is_mock:
        return RegisterResponse(message="Successfully registered (Mock Mode)")
    try:
        supabase_wrapper.get_client().auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
        return RegisterResponse(message="Registration successful. Verification email sent.")
    except Exception as e:
        logger.error(f"[Auth API] Registration failed for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/logout", response_model=RegisterResponse, status_code=status.HTTP_200_OK)
async def logout() -> RegisterResponse:
    logger.info("[Auth API] Logout requested.")
    if supabase_wrapper.is_mock:
        return RegisterResponse(message="Successfully logged out (Mock Mode)")
    try:
        supabase_wrapper.get_client().auth.sign_out()
        return RegisterResponse(message="Successfully logged out")
    except Exception as e:
        logger.error(f"[Auth API] Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}",
        )


@router.post("/oauth", response_model=OAuthResponse, status_code=status.HTTP_200_OK)
async def oauth(payload: OAuthRequest) -> OAuthResponse:
    logger.info(f"[Auth API] OAuth login attempt with provider: {payload.provider}")
    if supabase_wrapper.is_mock:
        return OAuthResponse(
            url=None,
            user_id="mock-oauth-123",
            email="oauth@mock.com",
            full_name="Mock OAuth User",
        )
    try:
        res = supabase_wrapper.get_client().auth.sign_in_with_oauth({"provider": payload.provider})
        url = getattr(res, "url", None)
        user = getattr(res, "user", None)
        if user:
            user_metadata = getattr(user, "user_metadata", {}) or {}
            full_name = user_metadata.get("full_name", "OAuth User")
            return OAuthResponse(url=url, user_id=user.id, email=user.email, full_name=full_name)
        return OAuthResponse(url=url)
    except Exception as e:
        logger.error(f"[Auth API] OAuth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth failed: {str(e)}"
        )
