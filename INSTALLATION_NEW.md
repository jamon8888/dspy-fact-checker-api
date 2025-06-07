# 🚀 **Installation Guide**

Complete installation guide for the DSPy-Enhanced Fact-Checker API Platform.

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 20GB free space
- **Network**: Internet access for Mistral OCR API

### **Required Services**
- **PostgreSQL**: 13+ (for database)
- **Redis**: 6+ (for caching and task queue)
- **Docker**: 20+ (optional, for containerized deployment)

### **API Keys Required**
- **Mistral API Key**: For OCR processing (primary)
- **OpenAI API Key**: For AI fact-checking (optional)
- **Anthropic API Key**: For Claude models (optional)

## 🐳 **Docker Installation (Recommended)**

### **Quick Start with Docker**
```bash
# 1. Clone repository
git clone https://github.com/your-repo/fact-checker.git
cd fact-checker

# 2. Copy environment template
cp .env.production .env

# 3. Edit environment file with your API keys
nano .env  # or use your preferred editor

# 4. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 5. Initialize database
docker-compose exec app python scripts/init_database.py

# 6. Verify installation
curl http://localhost:8000/health
```

### **Docker Services Included**
- **Application**: FastAPI server
- **PostgreSQL**: Database server
- **Redis**: Cache and task queue
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled tasks
- **Nginx**: Reverse proxy (production)

### **Docker Commands**
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs app
docker-compose logs postgres
docker-compose logs redis

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 🐍 **Python Installation (Manual)**

### **Step 1: System Dependencies**

#### **Ubuntu/Debian**
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-13 \
    postgresql-contrib \
    redis-server \
    tesseract-ocr \
    tesseract-ocr-eng \
    libpq-dev \
    build-essential \
    git \
    curl

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

#### **CentOS/RHEL/Fedora**
```bash
# Install system dependencies
sudo dnf install -y \
    python3.11 \
    python3-pip \
    postgresql-server \
    postgresql-contrib \
    redis \
    tesseract \
    tesseract-langpack-eng \
    postgresql-devel \
    gcc \
    git \
    curl

# Initialize PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl enable postgresql
sudo systemctl enable redis
```

#### **macOS**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql@13 redis tesseract git

# Start services
brew services start postgresql@13
brew services start redis
```

#### **Windows**
```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python311 postgresql redis tesseract git

# Start services
net start postgresql-x64-13
net start redis
```

### **Step 2: Database Setup**

#### **PostgreSQL Configuration**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE fact_checker_db;
CREATE USER fact_checker WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE fact_checker_db TO fact_checker;
ALTER USER fact_checker CREATEDB;
\q
```

#### **Redis Configuration**
```bash
# Edit Redis configuration (optional)
sudo nano /etc/redis/redis.conf

# Set password (recommended)
requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis
```

### **Step 3: Application Setup**

#### **Clone Repository**
```bash
git clone https://github.com/your-repo/fact-checker.git
cd fact-checker
```

#### **Create Virtual Environment**
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

#### **Install Python Dependencies**
```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-testing.txt
```

### **Step 4: Environment Configuration**

#### **Create Environment File**
```bash
# Copy production template
cp .env.production .env

# Edit with your configuration
nano .env
```

#### **Required Environment Variables**
```bash
# Database Configuration
DATABASE_URL=postgresql://fact_checker:your_secure_password@localhost:5432/fact_checker_db

# Redis Configuration
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# API Keys
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### **Step 5: Database Initialization**
```bash
# Initialize database schema
python scripts/init_database.py

# Verify database connection
python scripts/test_sync_db.py
```

### **Step 6: Start Application**

#### **Development Mode**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Production Mode**
```bash
# Single worker
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn (recommended for production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### **Background Workers**
```bash
# Start Celery worker (in separate terminal)
celery -A app.core.celery worker --loglevel=info

# Start Celery beat scheduler (in separate terminal)
celery -A app.core.celery beat --loglevel=info
```

## 🔧 **OCR Engine Setup**

### **Tesseract OCR (Local Fallback)**

#### **Ubuntu/Debian**
```bash
sudo apt install tesseract-ocr tesseract-ocr-eng
```

#### **macOS**
```bash
brew install tesseract
```

#### **Windows**
```powershell
choco install tesseract
```

#### **Additional Languages**
```bash
# Install additional language packs
sudo apt install tesseract-ocr-fra  # French
sudo apt install tesseract-ocr-deu  # German
sudo apt install tesseract-ocr-spa  # Spanish
```

### **RapidOCR (Local Fallback)**
```bash
# Already included in requirements.txt
pip install rapidocr-onnxruntime
```

### **Mistral OCR (Primary Engine)**
- Requires Mistral API key
- No local installation needed
- Configured via environment variables

## ✅ **Verification**

### **Health Check**
```bash
# Check application health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "dspy-fact-checker-api",
  "version": "1.0.0",
  "components": {
    "database": {"status": "connected"},
    "redis": {"status": "connected"},
    "celery": {"status": "healthy"}
  }
}
```

### **API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Test OCR Integration**
```bash
# Run OCR integration test
python scripts/test_mistral_fixed.py

# Expected output:
# [SUCCESS] All issues fixed! Mistral OCR API working perfectly!
```

### **Run Test Suite**
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_ocr_integration.py
pytest tests/test_api_endpoints.py

# Run production readiness test
python scripts/production_readiness_test.py
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep fact_checker

# Test connection
psql -h localhost -U fact_checker -d fact_checker_db
```

#### **Redis Connection Error**
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping
# Expected: PONG
```

#### **OCR Engine Issues**
```bash
# Test Tesseract installation
tesseract --version

# Test RapidOCR
python -c "import rapidocr_onnxruntime; print('RapidOCR OK')"

# Test Mistral API key
python scripts/test_mistral_minimal.py
```

#### **Permission Issues**
```bash
# Fix file permissions
chmod +x scripts/*.py

# Fix log directory permissions
mkdir -p logs
chmod 755 logs
```

---

**🎯 Installation complete! Your fact-checker platform is ready for production use.**
