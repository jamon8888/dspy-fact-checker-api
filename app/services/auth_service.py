"""
Authentication Service

Service for user authentication, registration, and session management.
"""

import logging
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole, UserStatus, APIKey, UserSession
from app.db.database import get_db

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY or "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """Service for authentication and user management."""
    
    def __init__(self):
        """Initialize the authentication service."""
        self.logger = logging.getLogger(__name__ + ".AuthService")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            if not self.verify_password(password, user.hashed_password):
                # Increment failed login attempts
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.commit()
                return None
            
            # Check if account is locked
            if user.account_locked_until and datetime.utcnow() < user.account_locked_until:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to too many failed login attempts"
                )
            
            # Check if account is active
            if not user.is_active or user.status == UserStatus.SUSPENDED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is not active"
                )
            
            # Reset failed login attempts and update last login
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.last_login = datetime.utcnow()
            db.commit()
            
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    async def register_user(
        self, 
        db: Session, 
        email: str, 
        password: str, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None
    ) -> User:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create new user
            hashed_password = self.get_password_hash(password)
            verification_token = secrets.token_urlsafe(32)
            
            user = User(
                email=email,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                company=company,
                role=UserRole.USER,
                status=UserStatus.PENDING_VERIFICATION,
                email_verification_token=verification_token
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # TODO: Send verification email
            self.logger.info(f"User registered: {email}")
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def verify_email(self, db: Session, token: str) -> bool:
        """Verify user email with verification token."""
        try:
            user = db.query(User).filter(User.email_verification_token == token).first()
            if not user:
                return False
            
            user.is_verified = True
            user.status = UserStatus.ACTIVE
            user.email_verification_token = None
            db.commit()
            
            self.logger.info(f"Email verified for user: {user.email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Email verification error: {e}")
            return False
    
    async def request_password_reset(self, db: Session, email: str) -> bool:
        """Request password reset for user."""
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                # Don't reveal if email exists
                return True
            
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.commit()
            
            # TODO: Send password reset email
            self.logger.info(f"Password reset requested for: {email}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset request error: {e}")
            return False
    
    async def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset user password with reset token."""
        try:
            user = db.query(User).filter(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.utcnow()
            ).first()
            
            if not user:
                return False
            
            user.hashed_password = self.get_password_hash(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            user.failed_login_attempts = 0
            user.account_locked_until = None
            db.commit()
            
            self.logger.info(f"Password reset for user: {user.email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset error: {e}")
            return False
    
    async def create_api_key(
        self, 
        db: Session, 
        user_id: int, 
        name: str, 
        description: Optional[str] = None,
        scopes: Optional[list] = None,
        expires_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """Create a new API key for user."""
        try:
            # Generate API key
            key = f"fc_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            key_prefix = key[:8]
            
            # Set expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Create API key record
            api_key = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                description=description,
                scopes=str(scopes) if scopes else None,
                expires_at=expires_at
            )
            
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            
            self.logger.info(f"API key created for user {user_id}: {name}")
            
            return key, api_key
            
        except Exception as e:
            self.logger.error(f"API key creation error: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    async def verify_api_key(self, db: Session, api_key: str) -> Optional[User]:
        """Verify API key and return associated user."""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            api_key_record = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
            if not api_key_record or not api_key_record.is_valid:
                return None
            
            # Update usage
            api_key_record.last_used = datetime.utcnow()
            api_key_record.usage_count += 1
            
            # Get user
            user = db.query(User).filter(User.id == api_key_record.user_id).first()
            if not user or not user.is_active:
                return None
            
            db.commit()
            return user
            
        except Exception as e:
            self.logger.error(f"API key verification error: {e}")
            return None
    
    async def create_session(
        self, 
        db: Session, 
        user_id: int, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Create a new user session."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                last_activity=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            
            return session_token
            
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
    
    async def verify_session(self, db: Session, session_token: str) -> Optional[User]:
        """Verify session token and return associated user."""
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if not session or not session.is_valid:
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            # Get user
            user = db.query(User).filter(User.id == session.user_id).first()
            if not user or not user.is_active:
                return None
            
            db.commit()
            return user
            
        except Exception as e:
            self.logger.error(f"Session verification error: {e}")
            return None
    
    async def revoke_session(self, db: Session, session_token: str) -> bool:
        """Revoke a user session."""
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                session.is_active = False
                session.ended_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Session revocation error: {e}")
            return False
    
    async def revoke_api_key(self, db: Session, api_key_id: int, user_id: int) -> bool:
        """Revoke an API key."""
        try:
            api_key = db.query(APIKey).filter(
                APIKey.id == api_key_id,
                APIKey.user_id == user_id
            ).first()
            
            if api_key:
                api_key.is_active = False
                api_key.revoked_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"API key revocation error: {e}")
            return False


# Global auth service instance
auth_service = AuthService()
