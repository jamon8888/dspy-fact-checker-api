#!/usr/bin/env python3
"""
Simple Database Initialization Script

Bypasses the complex configuration and directly initializes the database.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_database_engine():
    """Create database engine with direct URL."""
    database_url = os.getenv("DATABASE_URL", "postgresql://fact_checker:password123@localhost:5432/fact_checker_db")
    
    # Convert to sync URL for SQLAlchemy
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
    """Create database tables."""
    try:
        # Import models to register them
        from app.models.user import Base as UserBase
        from app.models.subscription import Base as SubscriptionBase

        # Create all tables
        UserBase.metadata.create_all(bind=engine)
        SubscriptionBase.metadata.create_all(bind=engine)

        print("[OK] Database tables created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create tables: {e}")
        return False

def create_admin_user(engine):
    """Create admin user."""
    try:
        from app.models.user import User
        from app.core.security import get_password_hash
        
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
            hashed_password=get_password_hash("admin123"),
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
        from app.models.subscription import SubscriptionPlan
        
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
    print("Starting simple database initialization...")

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
