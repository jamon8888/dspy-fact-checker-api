"""
Authentication API Endpoints

API endpoints for user authentication, registration, and session management.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session

from app.services.auth_service import auth_service
from app.models.user import User
from app.db.database import get_db, get_sync_db

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


class UserRegistration(BaseModel):
    """User registration request model."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login request model."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response model."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """User response model."""
    
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    role: str
    status: str
    is_verified: bool
    created_at: str


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordReset(BaseModel):
    """Password reset model."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class APIKeyRequest(BaseModel):
    """API key creation request model."""
    
    name: str = Field(..., max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days")


class APIKeyResponse(BaseModel):
    """API key response model."""
    
    id: int
    name: str
    key: str
    key_prefix: str
    description: Optional[str]
    expires_at: Optional[str]
    created_at: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_sync_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    # Try JWT token first
    payload = auth_service.verify_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user and user.is_active:
                return user
    
    # Try API key
    user = await auth_service.verify_api_key(db, token)
    if user:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegistration,
    db: Session = Depends(get_sync_db)
):
    """
    Register a new user account.

    Creates a new user account with email verification required.
    """
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        logger.info(f"Password validation passed for: {user_data.email}")
        user = await auth_service.register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company=user_data.company
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            company=user.company,
            role=user.role.value,
            status=user.status.value,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_sync_db)
):
    """
    Authenticate user and return access tokens.
    
    Returns JWT access token and refresh token for authenticated user.
    """
    try:
        user = await auth_service.authenticate_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})
        
        # Create session
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await auth_service.create_session(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,  # 30 minutes
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email address with verification token.
    """
    try:
        success = await auth_service.verify_email(db=db, token=token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/request-password-reset")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset for user account.
    
    Sends password reset email if account exists.
    """
    try:
        await auth_service.request_password_reset(
            db=db,
            email=request_data.email
        )
        
        return {"message": "Password reset email sent if account exists"}
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset user password with reset token.
    """
    try:
        success = await auth_service.reset_password(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        company=current_user.company,
        role=current_user.role.value,
        status=current_user.status.value,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the current user.
    """
    try:
        key, api_key = await auth_service.create_api_key(
            db=db,
            user_id=current_user.id,
            name=key_data.name,
            description=key_data.description,
            expires_days=key_data.expires_days
        )
        
        return APIKeyResponse(
            id=api_key.id,
            name=api_key.name,
            key=key,  # Only returned once
            key_prefix=api_key.key_prefix,
            description=api_key.description,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            created_at=api_key.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List user's API keys.
    """
    try:
        api_keys = db.query(auth_service.APIKey).filter(
            auth_service.APIKey.user_id == current_user.id
        ).all()
        
        return [
            {
                "id": key.id,
                "name": key.name,
                "key_prefix": key.key_prefix,
                "description": key.description,
                "is_active": key.is_active,
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "created_at": key.created_at.isoformat()
            }
            for key in api_keys
        ]
        
    except Exception as e:
        logger.error(f"API key listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    """
    try:
        success = await auth_service.revoke_api_key(
            db=db,
            api_key_id=key_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user (client should discard tokens).
    """
    return {"message": "Logged out successfully"}
