# ⚙️ **Configuration Guide**

Complete configuration reference for the DSPy-Enhanced Fact-Checker API Platform.

## 📋 **Environment Variables**

### **🔑 Required Configuration**

#### **API Keys**
```bash
# Mistral OCR API (Primary OCR Engine)
MISTRAL_API_KEY=your_mistral_api_key_here
# Get from: https://console.mistral.ai/

# OpenAI API (AI Fact-Checking)
OPENAI_API_KEY=your_openai_api_key_here
# Get from: https://platform.openai.com/api-keys

# Anthropic API (Claude Models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Get from: https://console.anthropic.com/
```

#### **Database Configuration**
```bash
# PostgreSQL Database URL
DATABASE_URL=postgresql://username:password@host:port/database_name
# Example: postgresql://factchecker:secure_pass@localhost:5432/fact_checker_db

# Database Pool Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

#### **Redis Configuration**
```bash
# Redis URL for caching and task queue
REDIS_URL=redis://username:password@host:port/database
# Example: redis://:redis_password@localhost:6379/0

# Redis Pool Settings
REDIS_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=50
```

#### **Security Configuration**
```bash
# JWT Secret Key (MUST be changed in production)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-256-bits-long

# JWT Token Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
```

### **🔧 Optional Configuration**

#### **Application Settings**
```bash
# Environment (development, staging, production)
ENVIRONMENT=production

# Application Settings
APP_NAME=DSPy-Enhanced Fact-Checker API
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

#### **OCR Engine Configuration**
```bash
# Primary OCR Engine
PRIMARY_OCR_ENGINE=mistral

# Fallback OCR Engines (comma-separated)
FALLBACK_OCR_ENGINES=tesseract,rapidocr

# OCR Settings
OCR_CONFIDENCE_THRESHOLD=0.8
OCR_MAX_PAGES=100
OCR_TIMEOUT_SECONDS=300
LOCAL_OCR_PRIORITY=false
```

#### **AI Model Configuration**
```bash
# Default AI Models
DEFAULT_FACT_CHECK_MODEL=gpt-4
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002
DEFAULT_LANGUAGE_MODEL=gpt-3.5-turbo

# Model Settings
MAX_TOKENS=4000
TEMPERATURE=0.1
TOP_P=0.9
FREQUENCY_PENALTY=0.0
PRESENCE_PENALTY=0.0
```

#### **File Upload Configuration**
```bash
# File Upload Settings
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=pdf,doc,docx,txt,png,jpg,jpeg,gif
UPLOAD_DIRECTORY=uploads/
TEMP_DIRECTORY=temp/

# Document Processing
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=3600
CLEANUP_TEMP_FILES=true
```

#### **Caching Configuration**
```bash
# Cache Settings
CACHE_TTL=3600
SESSION_TTL=86400
RATE_LIMIT_CACHE=true
OCR_RESULT_CACHE=true
FACT_CHECK_CACHE=true

# Cache Prefixes
CACHE_PREFIX=factchecker:
SESSION_PREFIX=session:
RATE_LIMIT_PREFIX=ratelimit:
```

#### **Monitoring & Observability**
```bash
# Sentry Error Tracking
SENTRY_DSN=your_sentry_dsn_here
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Prometheus Metrics
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_PATH=/metrics

# Logging
LOG_FORMAT=json
LOG_FILE=logs/app.log
LOG_ROTATION_SIZE=10MB
LOG_BACKUP_COUNT=5
```

#### **Security & CORS**
```bash
# CORS Settings
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE","OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# Security Headers
ALLOWED_HOSTS=["localhost","127.0.0.1","yourdomain.com"]
TRUSTED_HOSTS=["localhost","127.0.0.1"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

#### **Background Tasks**
```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC

# Task Settings
CELERY_WORKERS=4
TASK_RETRY_DELAY=60
TASK_MAX_RETRIES=3
TASK_SOFT_TIME_LIMIT=300
TASK_TIME_LIMIT=600
```

## 📁 **Configuration Files**

### **Application Configuration (app/core/config.py)**
```python
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "DSPy-Enhanced Fact-Checker API"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis
    redis_url: str
    redis_pool_size: int = 10
    
    # API Keys
    mistral_api_key: str
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # OCR Configuration
    primary_ocr_engine: str = "mistral"
    fallback_ocr_engines: List[str] = ["tesseract", "rapidocr"]
    ocr_confidence_threshold: float = 0.8
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### **Logging Configuration (logging.conf)**
```ini
[loggers]
keys=root,app,uvicorn

[handlers]
keys=console,file,rotating_file

[formatters]
keys=default,json

[logger_root]
level=INFO
handlers=console,rotating_file

[logger_app]
level=INFO
handlers=console,rotating_file
qualname=app
propagate=0

[logger_uvicorn]
level=INFO
handlers=console
qualname=uvicorn
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=default
args=(sys.stdout,)

[handler_file]
class=FileHandler
level=INFO
formatter=json
args=('logs/app.log',)

[handler_rotating_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=json
args=('logs/app.log', 'a', 10485760, 5)

[formatter_default]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_json]
class=pythonjsonlogger.jsonlogger.JsonFormatter
format=%(asctime)s %(name)s %(levelname)s %(message)s
```

### **Nginx Configuration (deployment/nginx/nginx.conf)**
```nginx
upstream app {
    server app:8000;
}

server {
    listen 80;
    server_name localhost;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # File upload size
    client_max_body_size 50M;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /health {
        access_log off;
        proxy_pass http://app;
    }
}
```

### **Docker Compose Configuration**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://factchecker:${DB_PASSWORD}@postgres:5432/factchecker
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=factchecker
      - POSTGRES_USER=factchecker
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./deployment/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    driver: bridge
```

## 🔧 **Environment-Specific Configurations**

### **Development Environment**
```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Use local services
DATABASE_URL=postgresql://factchecker:dev_password@localhost:5432/factchecker_dev
REDIS_URL=redis://localhost:6379/0

# Relaxed security for development
SECRET_KEY=dev-secret-key-not-for-production
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
ALLOWED_HOSTS=["*"]

# Development-specific settings
OCR_CONFIDENCE_THRESHOLD=0.7
CACHE_TTL=300
```

### **Staging Environment**
```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Staging database
DATABASE_URL=postgresql://factchecker:staging_password@staging-db:5432/factchecker_staging
REDIS_URL=redis://:staging_password@staging-redis:6379/0

# Production-like security
SECRET_KEY=staging-secret-key-different-from-prod
CORS_ORIGINS=["https://staging.yourdomain.com"]
ALLOWED_HOSTS=["staging.yourdomain.com"]

# Staging-specific settings
SENTRY_ENVIRONMENT=staging
RATE_LIMIT_REQUESTS_PER_MINUTE=200
```

### **Production Environment**
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Production database with connection pooling
DATABASE_URL=postgresql://factchecker:prod_password@prod-db:5432/factchecker
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Production Redis with password
REDIS_URL=redis://:prod_password@prod-redis:6379/0

# Strong security
SECRET_KEY=production-secret-key-256-bits-long-change-this
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com","www.yourdomain.com"]

# Production monitoring
SENTRY_DSN=your_production_sentry_dsn
PROMETHEUS_ENABLED=true

# Production performance
WORKERS=8
CELERY_WORKERS=16
CACHE_TTL=7200
```

## 🔍 **Configuration Validation**

### **Environment Validation Script**
```python
#!/usr/bin/env python3
"""
Configuration validation script
"""

import os
import sys
from urllib.parse import urlparse

def validate_config():
    """Validate all required configuration."""
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = [
        'MISTRAL_API_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate database URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        parsed = urlparse(db_url)
        if parsed.scheme != 'postgresql':
            errors.append("DATABASE_URL must use postgresql:// scheme")
    
    # Validate Redis URL
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        parsed = urlparse(redis_url)
        if parsed.scheme != 'redis':
            errors.append("REDIS_URL must use redis:// scheme")
    
    # Validate secret key length
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and len(secret_key) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters long")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration validation passed!")
    
    return len(errors) == 0

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)
```

### **Configuration Test Script**
```bash
#!/bin/bash
# test_config.sh

echo "Testing configuration..."

# Test database connection
python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Database connection: OK')
    conn.close()
except Exception as e:
    print(f'❌ Database connection: {e}')
"

# Test Redis connection
python -c "
import os
import redis
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('✅ Redis connection: OK')
except Exception as e:
    print(f'❌ Redis connection: {e}')
"

# Test Mistral API key
python -c "
import os
import requests
try:
    headers = {'Authorization': f'Bearer {os.getenv(\"MISTRAL_API_KEY\")}'}
    response = requests.get('https://api.mistral.ai/v1/models', headers=headers)
    if response.status_code == 200:
        print('✅ Mistral API key: OK')
    else:
        print(f'❌ Mistral API key: Invalid ({response.status_code})')
except Exception as e:
    print(f'❌ Mistral API key: {e}')
"

echo "Configuration test complete!"
```

---

**🎯 Complete configuration reference for optimal system performance**
