#!/usr/bin/env python3
"""
Production Readiness Test Suite
Comprehensive validation of all systems for production deployment
"""

import asyncio
import os
import sys
import time
import subprocess
import importlib
from typing import Dict, Any, List
from pathlib import Path

# Load production environment
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class ProductionReadinessTest:
    """Comprehensive production readiness test suite."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.results = []
        self.critical_failures = []
        self.warnings = []
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None, critical: bool = False):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": time.time(),
            "details": details or {},
            "critical": critical
        }
        self.results.append(result)
        
        if status == "FAIL" and critical:
            self.critical_failures.append(test_name)
        elif status == "FAIL":
            self.warnings.append(test_name)
        
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]"
        critical_marker = " [CRITICAL]" if critical else ""
        print(f"{status_icon} {test_name}{critical_marker}")
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_python_environment(self):
        """Test Python environment and version."""
        print("\n=== Testing Python Environment ===")
        
        try:
            python_version = sys.version_info
            
            self.log_test("python_version", "PASS" if python_version >= (3, 11) else "FAIL", {
                "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                "required": "3.11+",
                "compatible": python_version >= (3, 11)
            }, critical=True)
            
        except Exception as e:
            self.log_test("python_environment", "FAIL", {"error": str(e)}, critical=True)
    
    def test_critical_dependencies(self):
        """Test critical Python dependencies."""
        print("\n=== Testing Critical Dependencies ===")
        
        critical_deps = [
            ("fastapi", "0.100.0"),
            ("uvicorn", "0.20.0"),
            ("pydantic", "2.0.0"),
            ("sqlalchemy", "2.0.0"),
            ("redis", "4.0.0"),
            ("mistralai", "1.0.0"),
            ("docling", "1.0.0")
        ]
        
        for dep_name, min_version in critical_deps:
            try:
                module = importlib.import_module(dep_name)
                version = getattr(module, '__version__', 'unknown')
                
                self.log_test(f"dependency_{dep_name}", "PASS", {
                    "installed_version": version,
                    "minimum_required": min_version,
                    "status": "available"
                })
                
            except ImportError:
                self.log_test(f"dependency_{dep_name}", "FAIL", {
                    "error": "not installed",
                    "minimum_required": min_version
                }, critical=True)
    
    def test_ocr_dependencies(self):
        """Test OCR-specific dependencies."""
        print("\n=== Testing OCR Dependencies ===")
        
        ocr_deps = [
            "rapidocr_onnxruntime",
            "pytesseract", 
            "PIL",
            "cv2"
        ]
        
        for dep_name in ocr_deps:
            try:
                if dep_name == "cv2":
                    importlib.import_module("cv2")
                elif dep_name == "PIL":
                    importlib.import_module("PIL")
                else:
                    importlib.import_module(dep_name)
                
                self.log_test(f"ocr_dependency_{dep_name}", "PASS", {
                    "status": "available"
                })
                
            except ImportError:
                self.log_test(f"ocr_dependency_{dep_name}", "WARN", {
                    "error": "not installed",
                    "impact": "OCR fallback may not work"
                })
    
    def test_environment_variables(self):
        """Test critical environment variables."""
        print("\n=== Testing Environment Variables ===")
        
        critical_env_vars = [
            ("MISTRAL_API_KEY", True),
            ("DATABASE_URL", True),
            ("REDIS_URL", True),
            ("SECRET_KEY", True)
        ]
        
        optional_env_vars = [
            ("OPENAI_API_KEY", False),
            ("ANTHROPIC_API_KEY", False),
            ("SENTRY_DSN", False)
        ]
        
        for var_name, required in critical_env_vars:
            value = os.getenv(var_name)
            
            if value:
                self.log_test(f"env_var_{var_name}", "PASS", {
                    "value_preview": f"{value[:10]}..." if len(value) > 10 else "short_value",
                    "length": len(value),
                    "required": required
                })
            else:
                self.log_test(f"env_var_{var_name}", "FAIL", {
                    "error": "not set",
                    "required": required
                }, critical=required)
        
        for var_name, required in optional_env_vars:
            value = os.getenv(var_name)
            
            if value:
                self.log_test(f"optional_env_var_{var_name}", "PASS", {
                    "value_preview": f"{value[:10]}..." if len(value) > 10 else "short_value",
                    "required": required
                })
            else:
                self.log_test(f"optional_env_var_{var_name}", "WARN", {
                    "status": "not set",
                    "impact": "optional feature may not work"
                })
    
    def test_file_structure(self):
        """Test critical file structure."""
        print("\n=== Testing File Structure ===")
        
        critical_files = [
            "app/main.py",
            "app/core/config.py",
            "app/services/document_service.py",
            "app/core/document_processing/ocr/mistral_engine.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.prod.yml"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                self.log_test(f"file_{file_path.replace('/', '_').replace('.', '_')}", "PASS", {
                    "exists": True,
                    "size": f"{file_size} bytes"
                })
            else:
                self.log_test(f"file_{file_path.replace('/', '_').replace('.', '_')}", "FAIL", {
                    "exists": False,
                    "path": file_path
                }, critical=True)
    
    async def test_mistral_ocr_integration(self):
        """Test Mistral OCR integration."""
        print("\n=== Testing Mistral OCR Integration ===")
        
        try:
            from app.core.document_processing.ocr.mistral_engine import MistralOCREngine
            
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                self.log_test("mistral_ocr_integration", "FAIL", {
                    "error": "MISTRAL_API_KEY not set"
                }, critical=True)
                return
            
            # Test engine initialization
            engine = MistralOCREngine(
                api_key=api_key,
                model="mistral-ocr-latest"
            )
            
            # Test availability
            is_available = engine.is_available()
            
            # Get engine info
            engine_info = engine.get_engine_info()
            
            self.log_test("mistral_ocr_integration", "PASS", {
                "engine_available": is_available,
                "engine_name": engine_info.name,
                "engine_type": engine_info.type.value,
                "supports_bbox": engine_info.supports_bbox,
                "quality_rating": engine_info.quality_rating
            })
            
        except Exception as e:
            self.log_test("mistral_ocr_integration", "FAIL", {
                "error": str(e),
                "error_type": e.__class__.__name__
            }, critical=True)
    
    def test_docker_configuration(self):
        """Test Docker configuration."""
        print("\n=== Testing Docker Configuration ===")
        
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            
            if result.returncode == 0:
                docker_version = result.stdout.strip()
                self.log_test("docker_availability", "PASS", {
                    "version": docker_version,
                    "available": True
                })
                
                # Check Docker Compose
                result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
                
                if result.returncode == 0:
                    compose_version = result.stdout.strip()
                    self.log_test("docker_compose_availability", "PASS", {
                        "version": compose_version,
                        "available": True
                    })
                else:
                    self.log_test("docker_compose_availability", "WARN", {
                        "available": False,
                        "impact": "Docker Compose deployment not available"
                    })
            else:
                self.log_test("docker_availability", "WARN", {
                    "available": False,
                    "impact": "Docker deployment not available"
                })
                
        except FileNotFoundError:
            self.log_test("docker_availability", "WARN", {
                "available": False,
                "impact": "Docker deployment not available"
            })
    
    def test_system_resources(self):
        """Test system resources."""
        print("\n=== Testing System Resources ===")
        
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            self.log_test("system_memory", "PASS" if memory_gb >= 4 else "WARN", {
                "total_memory": f"{memory_gb:.1f} GB",
                "available_memory": f"{memory.available / (1024**3):.1f} GB",
                "memory_percent": f"{memory.percent}%",
                "recommended": "4GB+"
            })
            
            # Disk space check
            disk = psutil.disk_usage('.')
            disk_gb = disk.free / (1024**3)
            
            self.log_test("system_disk_space", "PASS" if disk_gb >= 10 else "WARN", {
                "free_space": f"{disk_gb:.1f} GB",
                "total_space": f"{disk.total / (1024**3):.1f} GB",
                "used_percent": f"{(disk.used / disk.total) * 100:.1f}%",
                "recommended": "10GB+ free"
            })
            
            # CPU check
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            self.log_test("system_cpu", "PASS", {
                "cpu_cores": cpu_count,
                "cpu_usage": f"{cpu_percent}%",
                "recommended": "2+ cores"
            })
            
        except ImportError:
            self.log_test("system_resources", "WARN", {
                "error": "psutil not available",
                "impact": "Cannot check system resources"
            })
    
    async def run_all_tests(self):
        """Run all production readiness tests."""
        print("Production Readiness Test Suite")
        print("=" * 80)
        print("Comprehensive validation for production deployment")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_python_environment()
        self.test_critical_dependencies()
        self.test_ocr_dependencies()
        self.test_environment_variables()
        self.test_file_structure()
        await self.test_mistral_ocr_integration()
        self.test_docker_configuration()
        self.test_system_resources()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate comprehensive report
        self.generate_final_report(total_time)
    
    def generate_final_report(self, total_time: float):
        """Generate final production readiness report."""
        print("\n" + "=" * 80)
        print("PRODUCTION READINESS ASSESSMENT REPORT")
        print("=" * 80)
        
        passed = sum(1 for result in self.results if result["status"] == "PASS")
        failed = sum(1 for result in self.results if result["status"] == "FAIL")
        warnings = sum(1 for result in self.results if result["status"] == "WARN")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Test Duration: {total_time:.2f} seconds")
        
        # Critical assessment
        if self.critical_failures:
            print(f"\n[CRITICAL FAILURES] {len(self.critical_failures)} issues:")
            for failure in self.critical_failures:
                print(f"  - {failure}")
            print("\n[VERDICT] NOT READY FOR PRODUCTION")
            print("[ACTION] Fix critical issues before deployment")
        elif failed > 0:
            print(f"\n[FAILURES] {failed} non-critical issues:")
            for result in self.results:
                if result["status"] == "FAIL" and not result["critical"]:
                    print(f"  - {result['test']}")
            print("\n[VERDICT] READY WITH CAUTION")
            print("[ACTION] Consider fixing issues for optimal deployment")
        else:
            print("\n[SUCCESS] ALL CRITICAL TESTS PASSED")
            print("[VERDICT] READY FOR PRODUCTION DEPLOYMENT")
            print("[ACTION] Proceed with deployment")
        
        if self.warnings:
            print(f"\n[WARNINGS] {len(self.warnings)} optional improvements:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Final recommendation
        readiness_score = (passed / total) * 100
        
        if readiness_score >= 90 and not self.critical_failures:
            print(f"\n[FINAL ASSESSMENT] EXCELLENT ({readiness_score:.1f}%)")
            print("[DEPLOYMENT STATUS] APPROVED FOR IMMEDIATE DEPLOYMENT")
        elif readiness_score >= 80 and not self.critical_failures:
            print(f"\n[FINAL ASSESSMENT] GOOD ({readiness_score:.1f}%)")
            print("[DEPLOYMENT STATUS] APPROVED WITH MONITORING")
        elif readiness_score >= 70:
            print(f"\n[FINAL ASSESSMENT] ACCEPTABLE ({readiness_score:.1f}%)")
            print("[DEPLOYMENT STATUS] CONDITIONAL APPROVAL")
        else:
            print(f"\n[FINAL ASSESSMENT] NEEDS IMPROVEMENT ({readiness_score:.1f}%)")
            print("[DEPLOYMENT STATUS] NOT RECOMMENDED")


async def main():
    """Main test function."""
    print("Starting Production Readiness Assessment...")
    print("This will validate all systems for production deployment.")
    print()
    
    tester = ProductionReadinessTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
