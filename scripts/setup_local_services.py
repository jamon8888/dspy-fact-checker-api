#!/usr/bin/env python3
"""
Local Services Setup Script

Sets up all required local services for production testing:
- PostgreSQL database
- Redis cache
- Qdrant vector database
"""

import subprocess
import time
import sys
import os
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages local Docker services for development."""
    
    def __init__(self):
        """Initialize service manager."""
        self.services = {
            "postgres": {
                "name": "fact-checker-postgres",
                "image": "postgres:15",
                "ports": ["5432:5432"],
                "environment": {
                    "POSTGRES_DB": "fact_checker_db",
                    "POSTGRES_USER": "fact_checker",
                    "POSTGRES_PASSWORD": "password123",
                    "PGDATA": "/var/lib/postgresql/data/pgdata"
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "health_check": ["pg_isready", "-U", "fact_checker", "-d", "fact_checker_db"]
            },
            "redis": {
                "name": "fact-checker-redis",
                "image": "redis:alpine",
                "ports": ["6379:6379"],
                "command": ["redis-server", "--requirepass", "password123"],
                "volumes": ["redis_data:/data"],
                "health_check": ["redis-cli", "ping"]
            },
            "qdrant": {
                "name": "fact-checker-qdrant",
                "image": "qdrant/qdrant",
                "ports": ["6333:6333", "6334:6334"],
                "environment": {
                    "QDRANT__SERVICE__HTTP_PORT": "6333",
                    "QDRANT__SERVICE__GRPC_PORT": "6334"
                },
                "volumes": ["qdrant_data:/qdrant/storage"],
                "health_check": ["wget", "--quiet", "--tries=1", "--spider", "http://localhost:6333/health"]
            }
        }
    
    def check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Docker found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Docker not found. Please install Docker first.")
            return False
    
    def create_volumes(self) -> bool:
        """Create Docker volumes for persistent data."""
        volumes = ["postgres_data", "redis_data", "qdrant_data"]
        
        for volume in volumes:
            try:
                # Check if volume exists
                result = subprocess.run(
                    ["docker", "volume", "inspect", volume],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    # Create volume
                    subprocess.run(
                        ["docker", "volume", "create", volume],
                        check=True
                    )
                    logger.info(f"Created volume: {volume}")
                else:
                    logger.info(f"Volume already exists: {volume}")
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create volume {volume}: {e}")
                return False
        
        return True
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        service_config = self.services.get(service_name)
        if not service_config:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        container_name = service_config["name"]
        
        try:
            # Stop container
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                check=False
            )
            
            # Remove container
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                check=False
            )
            
            logger.info(f"Stopped service: {service_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    def start_service(self, service_name: str) -> bool:
        """Start a specific service."""
        service_config = self.services.get(service_name)
        if not service_config:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        # Stop existing container first
        self.stop_service(service_name)
        
        # Build docker run command
        cmd = ["docker", "run", "-d"]
        
        # Add name
        cmd.extend(["--name", service_config["name"]])
        
        # Add ports
        for port in service_config.get("ports", []):
            cmd.extend(["-p", port])
        
        # Add environment variables
        for key, value in service_config.get("environment", {}).items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Add volumes
        for volume in service_config.get("volumes", []):
            cmd.extend(["-v", volume])
        
        # Add image
        cmd.append(service_config["image"])
        
        # Add command if specified
        if "command" in service_config:
            cmd.extend(service_config["command"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Started service: {service_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            logger.error(f"Command: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr}")
            return False
    
    def wait_for_service(self, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to be healthy."""
        service_config = self.services.get(service_name)
        if not service_config:
            return False
        
        container_name = service_config["name"]
        health_check = service_config.get("health_check")
        
        if not health_check:
            # No health check defined, just wait a bit
            time.sleep(5)
            return True
        
        logger.info(f"Waiting for {service_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Run health check inside container
                result = subprocess.run(
                    ["docker", "exec", container_name] + health_check,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"Service {service_name} is ready!")
                    return True
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass
            
            time.sleep(2)
        
        logger.error(f"Service {service_name} failed to become ready within {timeout} seconds")
        return False
    
    def start_all_services(self) -> bool:
        """Start all required services."""
        logger.info("🚀 Starting all local services...")
        
        if not self.check_docker():
            return False
        
        if not self.create_volumes():
            return False
        
        # Start services in order
        service_order = ["postgres", "redis", "qdrant"]
        
        for service_name in service_order:
            logger.info(f"Starting {service_name}...")
            
            if not self.start_service(service_name):
                return False
            
            if not self.wait_for_service(service_name):
                return False
        
        logger.info("✅ All services started successfully!")
        return True
    
    def stop_all_services(self) -> bool:
        """Stop all services."""
        logger.info("🛑 Stopping all local services...")
        
        success = True
        for service_name in self.services.keys():
            if not self.stop_service(service_name):
                success = False
        
        if success:
            logger.info("✅ All services stopped successfully!")
        else:
            logger.warning("⚠️  Some services failed to stop properly")
        
        return success
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        status = {}
        
        for service_name, service_config in self.services.items():
            container_name = service_config["name"]
            
            try:
                # Check if container is running
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if result.stdout.strip():
                    status[service_name] = {
                        "running": True,
                        "status": result.stdout.strip()
                    }
                else:
                    status[service_name] = {
                        "running": False,
                        "status": "Not running"
                    }
                    
            except subprocess.CalledProcessError:
                status[service_name] = {
                    "running": False,
                    "status": "Error checking status"
                }
        
        return status
    
    def print_service_status(self):
        """Print current service status."""
        status = self.get_service_status()
        
        print("\n" + "="*60)
        print("📊 LOCAL SERVICES STATUS")
        print("="*60)
        
        for service_name, service_status in status.items():
            service_config = self.services[service_name]
            ports = ", ".join(service_config.get("ports", []))
            
            status_icon = "🟢" if service_status["running"] else "🔴"
            print(f"{status_icon} {service_name.upper()}")
            print(f"   Status: {service_status['status']}")
            print(f"   Ports: {ports}")
            print()
        
        print("="*60)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage local services for fact-checker")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.action == "start":
        success = manager.start_all_services()
        if success:
            manager.print_service_status()
            print("\n🎉 All services are ready for testing!")
            print("\nNext steps:")
            print("1. Copy .env.production to .env and update API keys")
            print("2. Run: python -m uvicorn app.main:app --reload")
            print("3. Run tests: python scripts/production_test.py")
        sys.exit(0 if success else 1)
    
    elif args.action == "stop":
        success = manager.stop_all_services()
        sys.exit(0 if success else 1)
    
    elif args.action == "restart":
        manager.stop_all_services()
        time.sleep(2)
        success = manager.start_all_services()
        if success:
            manager.print_service_status()
        sys.exit(0 if success else 1)
    
    elif args.action == "status":
        manager.print_service_status()
        sys.exit(0)


if __name__ == "__main__":
    main()
