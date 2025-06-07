#!/usr/bin/env python3
"""
Production Testing Startup Script

Orchestrates the complete setup and testing process:
1. Sets up local services (PostgreSQL, Redis, Qdrant)
2. Initializes database with tables and data
3. Starts the application
4. Runs comprehensive API tests
5. Generates detailed reports
"""

import asyncio
import subprocess
import sys
import time
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionTestingOrchestrator:
    """Orchestrates the complete production testing process."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.app_process = None
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ is required")
            return False
        
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            logger.info("✅ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker is not available. Please install Docker.")
            return False
        
        # Check if required scripts exist
        required_scripts = [
            "setup_local_services.py",
            "init_database.py",
            "production_test.py"
        ]
        
        for script in required_scripts:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                logger.error(f"❌ Required script not found: {script}")
                return False
        
        logger.info("✅ All prerequisites met")
        return True
    
    def setup_environment(self) -> bool:
        """Set up environment configuration."""
        logger.info("🔧 Setting up environment...")
        
        env_file = self.project_root / ".env"
        env_production_file = self.project_root / ".env.production"
        
        # Check if .env exists
        if not env_file.exists():
            if env_production_file.exists():
                # Copy .env.production to .env
                import shutil
                shutil.copy2(env_production_file, env_file)
                logger.info("✅ Copied .env.production to .env")
                
                # Warn about API keys
                logger.warning("⚠️  Please update API keys in .env file:")
                logger.warning("   - OPENAI_API_KEY")
                logger.warning("   - ANTHROPIC_API_KEY") 
                logger.warning("   - MISTRAL_API_KEY")
                
                return True
            else:
                logger.error("❌ No .env or .env.production file found")
                return False
        else:
            logger.info("✅ .env file already exists")
            return True
    
    def start_services(self) -> bool:
        """Start all required local services."""
        logger.info("🚀 Starting local services...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / "setup_local_services.py"), "start"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Local services started successfully")
                return True
            else:
                logger.error(f"❌ Failed to start services: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Service startup timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error starting services: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize the database."""
        logger.info("🗄️  Initializing database...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / "init_database.py")],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Database initialized successfully")
                return True
            else:
                logger.error(f"❌ Failed to initialize database: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Database initialization timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            return False
    
    def start_application(self) -> bool:
        """Start the FastAPI application."""
        logger.info("🌐 Starting FastAPI application...")
        
        try:
            # Start the application in the background
            self.app_process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "0.0.0.0", 
                    "--port", "8000",
                    "--reload"
                ],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for application to start
            logger.info("⏳ Waiting for application to start...")
            time.sleep(10)  # Give the app time to start
            
            # Check if application is running
            if self.app_process.poll() is None:
                # Test if the application is responding
                import requests
                try:
                    response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ Application started successfully")
                        return True
                    else:
                        logger.error(f"❌ Application health check failed: {response.status_code}")
                        return False
                except requests.RequestException as e:
                    logger.error(f"❌ Application not responding: {e}")
                    return False
            else:
                logger.error("❌ Application failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting application: {e}")
            return False
    
    def run_tests(self) -> Dict[str, Any]:
        """Run comprehensive API tests."""
        logger.info("🧪 Running comprehensive API tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / "production_test.py")],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Print test output
            if result.stdout:
                print("\n" + "="*80)
                print("📊 TEST OUTPUT")
                print("="*80)
                print(result.stdout)
            
            if result.stderr:
                print("\n" + "="*80)
                print("⚠️  TEST WARNINGS/ERRORS")
                print("="*80)
                print(result.stderr)
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Tests timed out")
            return {"success": False, "error": "Tests timed out"}
        except Exception as e:
            logger.error(f"❌ Error running tests: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up...")
        
        # Stop the application
        if self.app_process and self.app_process.poll() is None:
            logger.info("Stopping application...")
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
                self.app_process.wait()
            logger.info("✅ Application stopped")
    
    def generate_final_report(self, test_results: Dict[str, Any]) -> str:
        """Generate final testing report."""
        report = []
        report.append("="*80)
        report.append("🎯 PRODUCTION TESTING FINAL REPORT")
        report.append("="*80)
        
        if test_results.get("success"):
            report.append("🎉 OVERALL STATUS: PASSED")
            report.append("")
            report.append("✅ All systems are operational and ready for production!")
            report.append("")
            report.append("📋 What was tested:")
            report.append("  • Health and monitoring endpoints")
            report.append("  • Authentication and authorization")
            report.append("  • Core fact-checking functionality")
            report.append("  • Document and URL processing")
            report.append("  • OCR capabilities")
            report.append("  • Billing and subscription system")
            report.append("  • Admin functions")
            report.append("  • Error handling and security")
            report.append("  • Performance under load")
            report.append("")
            report.append("🚀 Next steps:")
            report.append("  1. Update API keys in .env file")
            report.append("  2. Configure external services (Stripe, email, etc.)")
            report.append("  3. Set up production monitoring")
            report.append("  4. Deploy to production environment")
        else:
            report.append("❌ OVERALL STATUS: FAILED")
            report.append("")
            report.append("⚠️  Some tests failed. Please review the issues above.")
            report.append("")
            report.append("🔧 Common issues:")
            report.append("  • Missing API keys in .env file")
            report.append("  • Services not running properly")
            report.append("  • Database connection issues")
            report.append("  • Network connectivity problems")
        
        report.append("")
        report.append("📄 Detailed test results saved to test_results_*.json")
        report.append("="*80)
        
        return "\n".join(report)
    
    async def run_complete_testing(self) -> bool:
        """Run the complete testing process."""
        logger.info("🎬 Starting complete production testing process...")
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Step 2: Setup environment
            if not self.setup_environment():
                return False
            
            # Step 3: Start services
            if not self.start_services():
                return False
            
            # Step 4: Initialize database
            if not self.initialize_database():
                return False
            
            # Step 5: Start application
            if not self.start_application():
                return False
            
            # Step 6: Run tests
            test_results = self.run_tests()
            
            # Step 7: Generate final report
            final_report = self.generate_final_report(test_results)
            print("\n" + final_report)
            
            return test_results.get("success", False)
            
        except KeyboardInterrupt:
            logger.info("🛑 Testing interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup()


async def main():
    """Main function."""
    orchestrator = ProductionTestingOrchestrator()
    
    print("🚀 FACT-CHECKER PRODUCTION TESTING")
    print("="*50)
    print("This script will:")
    print("1. ✅ Check prerequisites")
    print("2. 🔧 Setup environment")
    print("3. 🐳 Start Docker services")
    print("4. 🗄️  Initialize database")
    print("5. 🌐 Start application")
    print("6. 🧪 Run comprehensive tests")
    print("7. 📊 Generate reports")
    print("="*50)
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    success = await orchestrator.run_complete_testing()
    
    if success:
        print("\n🎉 Production testing completed successfully!")
        print("The system is ready for production deployment.")
        sys.exit(0)
    else:
        print("\n❌ Production testing failed!")
        print("Please review the errors and try again.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
