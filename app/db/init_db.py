"""
Database initialization utilities for the DSPy-Enhanced Fact-Checker API Platform.
"""

import asyncio
import logging
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import init_database, create_tables, close_database, DatabaseHealthCheck
from app.db.models import *  # Import all models
from app.models import *  # Import new user and billing models
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def init_db() -> bool:
    """Initialize the database with all tables."""
    try:
        logger.info("Initializing database...")
        
        # Initialize database connection
        await init_database()
        
        # Create all tables
        await create_tables()
        
        # Verify database health
        health_check = DatabaseHealthCheck()
        is_healthy = await health_check.check_connection()
        
        if is_healthy:
            logger.info("Database initialized successfully")
            
            # Log connection info
            conn_info = await health_check.get_connection_info()
            logger.info(f"Database info: {conn_info}")
            
            return True
        else:
            logger.error("Database health check failed after initialization")
            return False
            
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        return False


async def reset_db() -> bool:
    """Reset the database by dropping and recreating all tables."""
    try:
        logger.warning("Resetting database - this will delete all data!")
        
        # Initialize database connection
        await init_database()
        
        # Import the drop_tables function
        from app.db.database import drop_tables
        
        # Drop all tables
        await drop_tables()
        
        # Recreate all tables
        await create_tables()
        
        # Verify database health
        health_check = DatabaseHealthCheck()
        is_healthy = await health_check.check_connection()
        
        if is_healthy:
            logger.info("Database reset completed successfully")
            return True
        else:
            logger.error("Database health check failed after reset")
            return False
            
    except SQLAlchemyError as e:
        logger.error(f"Database reset failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database reset: {e}")
        return False


async def check_db_health() -> dict:
    """Check database health and return status information."""
    try:
        # Initialize database if not already done
        await init_database()
        
        health_check = DatabaseHealthCheck()
        
        # Check connection
        is_connected = await health_check.check_connection()
        
        # Get connection info
        conn_info = await health_check.get_connection_info()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "connection_info": conn_info
        }
        
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }


async def create_sample_data() -> bool:
    """Create sample data for testing purposes."""
    try:
        logger.info("Creating sample data...")
        
        from app.db.database import get_db_session
        from app.db.models import ProcessingJob, Document, TextAnalysis
        import uuid
        import json
        from datetime import datetime
        
        async with get_db_session() as session:
            # Create a sample processing job
            sample_job = ProcessingJob(
                id=str(uuid.uuid4()),
                job_type="document",
                status="completed",
                priority="normal",
                input_data={"filename": "sample_document.pdf", "file_size": 1024000},
                processing_options={"perform_ocr": True, "extract_tables": True},
                result_data={"claims_found": 5, "accuracy_score": 0.85},
                progress=100.0,
                current_stage="completed",
                actual_processing_time=45.2,
                estimated_cost=0.05,
                actual_cost=0.048
            )
            session.add(sample_job)
            
            # Create a sample document
            sample_document = Document(
                id=str(uuid.uuid4()),
                filename="sample_document.pdf",
                original_filename="Sample Research Paper.pdf",
                file_type="pdf",
                file_size=1024000,
                processing_job_id=sample_job.id,
                title="Sample Research Paper on Climate Change",
                author="Dr. Jane Smith",
                page_count=15,
                word_count=5000,
                language="en",
                extracted_text="This is a sample extracted text from the document...",
                overall_verdict="MOSTLY_ACCURATE",
                accuracy_score=0.85,
                is_processed=True
            )
            session.add(sample_document)
            
            # Create a sample text analysis
            sample_text = TextAnalysis(
                id=str(uuid.uuid4()),
                processing_job_id=str(uuid.uuid4()),
                input_text="Climate change is a significant global challenge that requires immediate action.",
                optimization_level="standard",
                language="en",
                word_count=12,
                character_count=85,
                sentence_count=1,
                paragraph_count=1,
                reading_time=0.1,
                complexity_score=0.6,
                overall_verdict="SUPPORTED",
                confidence_score=0.92,
                claims_analyzed=1,
                processing_time=2.3,
                is_processed=True
            )
            session.add(sample_text)
            
            # Commit the changes
            await session.commit()
            
        logger.info("Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        return False


async def cleanup_db() -> None:
    """Clean up database connections."""
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# CLI functions for database management
async def main():
    """Main function for database initialization."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            success = await init_db()
            if success:
                print("Database initialized successfully")
            else:
                print("Database initialization failed")
                sys.exit(1)

        elif command == "reset":
            success = await reset_db()
            if success:
                print("Database reset successfully")
            else:
                print("Database reset failed")
                sys.exit(1)

        elif command == "health":
            health = await check_db_health()
            print(f"Database health: {health}")

        elif command == "sample":
            success = await create_sample_data()
            if success:
                print("Sample data created successfully")
            else:
                print("Failed to create sample data")
                sys.exit(1)
                
        else:
            print("Usage: python -m app.db.init_db [init|reset|health|sample]")
            sys.exit(1)
    else:
        # Default: initialize database
        success = await init_db()
        if success:
            print("Database initialized successfully")
        else:
            print("Database initialization failed")
            sys.exit(1)
    
    # Clean up
    await cleanup_db()


if __name__ == "__main__":
    asyncio.run(main())
