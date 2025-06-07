#!/usr/bin/env python3
"""
Database Initialization Script

Initializes the PostgreSQL database with all required tables and data.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import Base as UserBase
from app.models.subscription import Base as SubscriptionBase
from app.db.database import get_database_url

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Database initialization and setup."""
    
    def __init__(self):
        """Initialize database manager."""
        self.settings = get_settings()
        self.database_url = get_database_url()
        self.engine = None
        self.session_factory = None
    
    def create_engine(self):
        """Create database engine."""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False  # Set to True for SQL debugging
            )
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("Database engine created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create all database tables."""
        try:
            # Create all tables from all models
            UserBase.metadata.create_all(bind=self.engine)
            SubscriptionBase.metadata.create_all(bind=self.engine)
            
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """Create additional database indexes for performance."""
        indexes = [
            # User table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
            
            # API keys indexes
            "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);",
            
            # Subscription indexes
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id);",
            
            # Usage records indexes
            "CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_usage_records_date ON usage_records(date);",
            "CREATE INDEX IF NOT EXISTS idx_usage_records_endpoint ON usage_records(endpoint);",
            
            # Fact check results indexes (if table exists)
            "CREATE INDEX IF NOT EXISTS idx_fact_check_results_user_id ON fact_check_results(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_fact_check_results_created_at ON fact_check_results(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_fact_check_results_status ON fact_check_results(status);",
        ]
        
        try:
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Index creation warning: {e}")
                        # Continue with other indexes
            
            logger.info("Database indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            return False
    
    def insert_default_data(self) -> bool:
        """Insert default data into the database."""
        try:
            with self.session_factory() as session:
                # Insert default subscription plans
                from app.models.subscription import SubscriptionPlan
                
                # Check if plans already exist
                existing_plans = session.query(SubscriptionPlan).count()
                if existing_plans > 0:
                    logger.info("Subscription plans already exist, skipping insertion")
                    return True
                
                default_plans = [
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
                
                for plan in default_plans:
                    session.add(plan)
                
                session.commit()
                logger.info("Default subscription plans inserted successfully")
                
            return True
        except Exception as e:
            logger.error(f"Failed to insert default data: {e}")
            return False
    
    def create_admin_user(self) -> bool:
        """Create default admin user for testing."""
        try:
            with self.session_factory() as session:
                from app.models.user import User
                from app.core.security import get_password_hash
                
                # Check if admin user already exists
                admin_user = session.query(User).filter(User.email == "admin@fact-checker.com").first()
                if admin_user:
                    logger.info("Admin user already exists")
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
                
                logger.info("Admin user created successfully")
                logger.info("Admin credentials: admin@fact-checker.com / admin123")
                
            return True
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            return False
    
    def verify_setup(self) -> bool:
        """Verify database setup is complete."""
        try:
            with self.session_factory() as session:
                # Check tables exist
                from app.models.user import User
                from app.models.subscription import SubscriptionPlan
                
                user_count = session.query(User).count()
                plan_count = session.query(SubscriptionPlan).count()
                
                logger.info(f"Database verification:")
                logger.info(f"  Users: {user_count}")
                logger.info(f"  Subscription plans: {plan_count}")
                
                if plan_count >= 4:  # Should have 4 default plans
                    logger.info("✅ Database setup verification passed")
                    return True
                else:
                    logger.error("❌ Database setup verification failed")
                    return False
                    
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Complete database initialization process."""
        logger.info("🚀 Starting database initialization...")
        
        steps = [
            ("Creating database engine", self.create_engine),
            ("Testing database connection", self.test_connection),
            ("Creating database tables", self.create_tables),
            ("Creating database indexes", self.create_indexes),
            ("Inserting default data", self.insert_default_data),
            ("Creating admin user", self.create_admin_user),
            ("Verifying setup", self.verify_setup)
        ]
        
        for step_name, step_function in steps:
            logger.info(f"📋 {step_name}...")
            if not step_function():
                logger.error(f"❌ Failed: {step_name}")
                return False
            logger.info(f"✅ Completed: {step_name}")
        
        logger.info("🎉 Database initialization completed successfully!")
        return True


def main():
    """Main function."""
    # Load environment variables
    from dotenv import load_dotenv
    
    # Try to load .env file
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info("Loaded environment from .env file")
    else:
        logger.warning("No .env file found, using environment variables")
    
    # Initialize database
    initializer = DatabaseInitializer()
    success = initializer.initialize_database()
    
    if success:
        print("\n" + "="*60)
        print("🎯 DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print("✅ All tables created")
        print("✅ Indexes created")
        print("✅ Default data inserted")
        print("✅ Admin user created")
        print("\n📋 Next steps:")
        print("1. Start the application: python -m uvicorn app.main:app --reload")
        print("2. Run tests: python scripts/production_test.py")
        print("\n🔑 Admin credentials:")
        print("   Email: admin@fact-checker.com")
        print("   Password: admin123")
        print("="*60)
    else:
        print("\n❌ Database initialization failed!")
        print("Please check the logs for details.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
