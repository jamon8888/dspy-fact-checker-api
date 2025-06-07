#!/usr/bin/env python3
"""
Standalone Database Initialization Script

Creates database tables and initial data without importing app configuration.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, Float, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import hashlib
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create base class
Base = declarative_base()

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Account status and role
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
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
    notification_preferences = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly
    features = Column(JSON, nullable=True)
    limits = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(String(50), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False)
    
    # Billing information
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    usage_limit = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    cancelled_at = Column(DateTime, nullable=True)

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    
    # Request details
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Billing
    cost = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions and restrictions
    scopes = Column(Text, nullable=True)
    rate_limit = Column(Integer, nullable=True)
    ip_whitelist = Column(Text, nullable=True)
    
    # Status and usage
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_database_engine():
    """Create database engine."""
    database_url = os.getenv("DATABASE_URL", "postgresql://fact_checker:password123@localhost:5432/fact_checker_db")
    
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database: {database_url}")
    
    engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False
    )
    
    return engine

def test_connection(engine):
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("[OK] Database connection successful")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False

def create_tables(engine):
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create tables: {e}")
        return False

def create_admin_user(engine):
    """Create admin user."""
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if admin exists
        admin = session.query(User).filter(User.email == "admin@fact-checker.com").first()
        if admin:
            print("[OK] Admin user already exists")
            session.close()
            return True
        
        # Create admin user
        admin_user = User(
            email="admin@fact-checker.com",
            full_name="System Administrator",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        
        session.add(admin_user)
        session.commit()
        session.close()
        
        print("[OK] Admin user created successfully")
        print("   Email: admin@fact-checker.com")
        print("   Password: admin123")
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to create admin user: {e}")
        return False

def create_subscription_plans(engine):
    """Create default subscription plans."""
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if plans exist
        existing_plans = session.query(SubscriptionPlan).count()
        if existing_plans > 0:
            print("[OK] Subscription plans already exist")
            session.close()
            return True
        
        # Create default plans
        plans = [
            SubscriptionPlan(
                id="free",
                name="Free",
                description="Free tier with basic features",
                price=0.0,
                billing_cycle="monthly",
                features={
                    "requests_per_month": 100,
                    "models": ["gpt-3.5-turbo"],
                    "document_processing": False,
                    "url_processing": False,
                    "ocr_processing": False,
                    "priority_support": False,
                    "api_access": True,
                    "export_formats": ["json"]
                },
                limits={
                    "max_file_size_mb": 5,
                    "max_requests_per_minute": 10,
                    "max_concurrent_requests": 1
                },
                is_active=True
            ),
            SubscriptionPlan(
                id="starter",
                name="Starter",
                description="Perfect for individuals and small projects",
                price=29.0,
                billing_cycle="monthly",
                features={
                    "requests_per_month": 5000,
                    "models": ["gpt-3.5-turbo", "gpt-4"],
                    "document_processing": True,
                    "url_processing": True,
                    "ocr_processing": False,
                    "priority_support": False,
                    "api_access": True,
                    "export_formats": ["json", "csv"]
                },
                limits={
                    "max_file_size_mb": 25,
                    "max_requests_per_minute": 50,
                    "max_concurrent_requests": 3
                },
                is_active=True
            ),
            SubscriptionPlan(
                id="professional",
                name="Professional",
                description="Advanced features for professionals and teams",
                price=99.0,
                billing_cycle="monthly",
                features={
                    "requests_per_month": 25000,
                    "models": ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral"],
                    "document_processing": True,
                    "url_processing": True,
                    "ocr_processing": True,
                    "priority_support": True,
                    "api_access": True,
                    "export_formats": ["json", "csv", "pdf", "xlsx"]
                },
                limits={
                    "max_file_size_mb": 100,
                    "max_requests_per_minute": 200,
                    "max_concurrent_requests": 10
                },
                is_active=True
            ),
            SubscriptionPlan(
                id="enterprise",
                name="Enterprise",
                description="Full-featured plan for large organizations",
                price=299.0,
                billing_cycle="monthly",
                features={
                    "requests_per_month": 100000,
                    "models": ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral", "custom"],
                    "document_processing": True,
                    "url_processing": True,
                    "ocr_processing": True,
                    "priority_support": True,
                    "api_access": True,
                    "export_formats": ["json", "csv", "pdf", "xlsx", "xml"],
                    "custom_models": True,
                    "dedicated_support": True,
                    "sla_guarantee": True
                },
                limits={
                    "max_file_size_mb": 500,
                    "max_requests_per_minute": 1000,
                    "max_concurrent_requests": 50
                },
                is_active=True
            )
        ]
        
        for plan in plans:
            session.add(plan)
        
        session.commit()
        session.close()
        
        print("[OK] Subscription plans created successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to create subscription plans: {e}")
        return False

def main():
    """Main initialization function."""
    print("Starting standalone database initialization...")
    
    # Create engine
    try:
        engine = create_database_engine()
    except Exception as e:
        print(f"[FAIL] Failed to create database engine: {e}")
        return False
    
    # Test connection
    if not test_connection(engine):
        return False
    
    # Create tables
    if not create_tables(engine):
        return False
    
    # Create admin user
    if not create_admin_user(engine):
        return False
    
    # Create subscription plans
    if not create_subscription_plans(engine):
        return False
    
    print("\nDatabase initialization completed successfully!")
    print("\nSummary:")
    print("[OK] Database connection established")
    print("[OK] Tables created")
    print("[OK] Admin user created (admin@fact-checker.com / admin123)")
    print("[OK] Subscription plans created")
    print("\nReady to start the application!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
