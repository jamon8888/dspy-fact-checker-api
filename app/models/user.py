"""
User Model

Database model for user management and authentication.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.base_class import Base


class UserRole(str, enum.Enum):
    """User roles for access control."""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Account status and role
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Authentication and security
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime, nullable=True)
    
    # API access
    api_key = Column(String(255), unique=True, index=True, nullable=True)
    api_key_created_at = Column(DateTime, nullable=True)
    api_key_last_used = Column(DateTime, nullable=True)
    
    # Preferences and settings
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    notification_preferences = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split("@")[0]
    
    @property
    def is_premium_user(self):
        """Check if user has premium access."""
        return self.role in [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN]
    
    @property
    def is_enterprise_user(self):
        """Check if user has enterprise access."""
        return self.role in [UserRole.ENTERPRISE, UserRole.ADMIN]
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if user can access a specific feature."""
        feature_permissions = {
            "basic_fact_checking": [UserRole.USER, UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN],
            "advanced_fact_checking": [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN],
            "bulk_processing": [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN],
            "api_access": [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN],
            "custom_models": [UserRole.ENTERPRISE, UserRole.ADMIN],
            "white_label": [UserRole.ENTERPRISE, UserRole.ADMIN],
            "admin_panel": [UserRole.ADMIN],
        }
        
        allowed_roles = feature_permissions.get(feature, [])
        return self.role in allowed_roles


class APIKey(Base):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few characters for display
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions and restrictions
    scopes = Column(Text, nullable=True)  # JSON array of allowed scopes
    rate_limit = Column(Integer, nullable=True)  # Requests per minute
    ip_whitelist = Column(Text, nullable=True)  # JSON array of allowed IPs
    
    # Status and usage
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    @property
    def is_expired(self):
        """Check if API key is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_valid(self):
        """Check if API key is valid for use."""
        return (
            self.is_active and 
            not self.is_expired and 
            self.revoked_at is None
        )


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)  # JSON string
    location = Column(String(100), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if session is valid."""
        return self.is_active and not self.is_expired and self.ended_at is None


class UserPreferences(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    usage_alerts = Column(Boolean, default=True, nullable=False)
    billing_notifications = Column(Boolean, default=True, nullable=False)
    security_alerts = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Processing preferences
    default_model = Column(String(50), nullable=True)
    preferred_language = Column(String(10), default="en", nullable=False)
    auto_save_results = Column(Boolean, default=True, nullable=False)
    result_retention_days = Column(Integer, default=30, nullable=False)
    
    # UI preferences
    theme = Column(String(20), default="light", nullable=False)
    dashboard_layout = Column(Text, nullable=True)  # JSON string
    items_per_page = Column(Integer, default=25, nullable=False)
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False, nullable=False)
    analytics_consent = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id})>"
