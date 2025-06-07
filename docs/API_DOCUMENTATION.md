# 📚 **API Documentation**

Complete API reference for the DSPy-Enhanced Fact-Checker API Platform.

## 🌐 **Base Information**

- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: JWT Bearer Token
- **Content-Type**: `application/json`
- **API Version**: v1.0.0

## 🔐 **Authentication**

### **Register User**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123",
  "full_name": "John Doe",
  "organization": "Example Corp"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user_id": "uuid-here",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### **Login**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "user_id": "uuid-here",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

### **Refresh Token**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 📄 **Document Processing**

### **Upload Document**
```http
POST /api/v1/documents/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: document.pdf
language: en
ocr_engine: mistral
extract_images: true
extract_tables: true
```

**Response:**
```json
{
  "status": "success",
  "message": "Document uploaded successfully",
  "data": {
    "document_id": "uuid-here",
    "filename": "document.pdf",
    "file_size": 1048576,
    "mime_type": "application/pdf",
    "status": "uploaded",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### **Process Document**
```http
POST /api/v1/documents/{document_id}/process
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "ocr_engine": "mistral",
  "language": "en",
  "extract_images": true,
  "extract_tables": true,
  "confidence_threshold": 0.8
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document processing started",
  "data": {
    "task_id": "uuid-here",
    "document_id": "uuid-here",
    "status": "processing",
    "estimated_completion": "2024-01-01T00:05:00Z"
  }
}
```

### **Get Processing Status**
```http
GET /api/v1/documents/{document_id}/status
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "document_id": "uuid-here",
    "status": "completed",
    "progress": 100,
    "processing_time": 45.2,
    "ocr_results": {
      "engine_used": "mistral",
      "confidence": 0.95,
      "text_length": 5420,
      "pages_processed": 10
    },
    "completed_at": "2024-01-01T00:05:00Z"
  }
}
```

### **Download Processed Document**
```http
GET /api/v1/documents/{document_id}/download
Authorization: Bearer {access_token}
Accept: application/json
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "document_id": "uuid-here",
    "extracted_text": "Full document text here...",
    "metadata": {
      "pages": 10,
      "word_count": 1250,
      "character_count": 5420,
      "language": "en",
      "confidence": 0.95
    },
    "images": [
      {
        "page": 1,
        "bbox": [100, 200, 300, 400],
        "confidence": 0.98
      }
    ],
    "tables": [
      {
        "page": 3,
        "rows": 5,
        "columns": 4,
        "data": [["Header1", "Header2"], ["Data1", "Data2"]]
      }
    ]
  }
}
```

## 🔍 **Fact-Checking**

### **Fact-Check Text**
```http
POST /api/v1/fact-check/text
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "text": "The Earth is flat and the moon is made of cheese.",
  "language": "en",
  "model": "gpt-4",
  "confidence_threshold": 0.7,
  "include_sources": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Fact-check completed",
  "data": {
    "fact_check_id": "uuid-here",
    "overall_score": 0.15,
    "overall_verdict": "mostly_false",
    "claims": [
      {
        "claim": "The Earth is flat",
        "verdict": "false",
        "confidence": 0.98,
        "evidence": [
          {
            "source": "NASA",
            "url": "https://nasa.gov/earth-round",
            "snippet": "Scientific evidence proves Earth is spherical",
            "credibility": 0.95
          }
        ]
      },
      {
        "claim": "The moon is made of cheese",
        "verdict": "false",
        "confidence": 0.99,
        "evidence": [
          {
            "source": "Apollo Mission Data",
            "url": "https://nasa.gov/apollo-samples",
            "snippet": "Moon samples show rocky composition",
            "credibility": 0.98
          }
        ]
      }
    ],
    "processing_time": 8.5,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### **Fact-Check Document**
```http
POST /api/v1/fact-check/document
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "document_id": "uuid-here",
  "claims_to_check": ["specific claim 1", "specific claim 2"],
  "model": "gpt-4",
  "confidence_threshold": 0.7,
  "include_sources": true
}
```

### **Get Fact-Check Results**
```http
GET /api/v1/fact-check/{fact_check_id}
Authorization: Bearer {access_token}
```

## 📊 **Analytics & Monitoring**

### **User Statistics**
```http
GET /api/v1/analytics/user/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "documents_processed": 45,
    "fact_checks_performed": 123,
    "total_processing_time": 3600,
    "accuracy_score": 0.92,
    "usage_this_month": {
      "documents": 12,
      "fact_checks": 34,
      "api_calls": 156
    }
  }
}
```

### **System Health**
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "dspy-fact-checker-api",
  "version": "1.0.0",
  "timestamp": 1704067200,
  "components": {
    "database": {
      "status": "connected",
      "response_time": 5.2
    },
    "redis": {
      "status": "connected",
      "memory_usage": "45%"
    },
    "qdrant": {
      "status": "connected",
      "collections": 3
    },
    "celery": {
      "status": "healthy",
      "active_tasks": 2,
      "workers": 4
    }
  }
}
```

## 🔧 **Configuration**

### **Get User Preferences**
```http
GET /api/v1/user/preferences
Authorization: Bearer {access_token}
```

### **Update User Preferences**
```http
PUT /api/v1/user/preferences
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "default_ocr_engine": "mistral",
  "default_language": "en",
  "confidence_threshold": 0.8,
  "include_sources": true,
  "email_notifications": true
}
```

## 📝 **Error Responses**

### **Standard Error Format**
```json
{
  "status": "error",
  "message": "Detailed error message",
  "error_code": "VALIDATION_ERROR",
  "request_id": "uuid-here",
  "timestamp": "2024-01-01T00:00:00Z",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### **Common Error Codes**

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid token |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `PROCESSING_ERROR` | 500 | Internal processing error |
| `OCR_ENGINE_ERROR` | 503 | OCR service unavailable |

## 📊 **Rate Limits**

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Document Upload | 20 requests | 1 hour |
| Document Processing | 50 requests | 1 hour |
| Fact-Checking | 100 requests | 1 hour |
| Analytics | 200 requests | 1 hour |

## 🔍 **Query Parameters**

### **Pagination**
```http
GET /api/v1/documents?page=1&limit=20&sort=created_at&order=desc
```

### **Filtering**
```http
GET /api/v1/fact-checks?status=completed&date_from=2024-01-01&date_to=2024-01-31
```

### **Search**
```http
GET /api/v1/documents/search?q=climate%20change&language=en
```

## 🧪 **Testing**

### **Test Authentication**
```bash
# Register test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### **Test Document Upload**
```bash
# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_document.pdf" \
  -F "language=en"
```

### **Test Fact-Checking**
```bash
# Fact-check text
curl -X POST http://localhost:8000/api/v1/fact-check/text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"The Earth is round","language":"en"}'
```

## 📚 **SDKs and Libraries**

### **Python SDK**
```python
from fact_checker_sdk import FactCheckerClient

client = FactCheckerClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)

# Upload and process document
document = client.documents.upload("document.pdf")
result = client.documents.process(document.id)

# Fact-check text
fact_check = client.fact_check.text("The Earth is round")
```

### **JavaScript SDK**
```javascript
import { FactCheckerClient } from 'fact-checker-js-sdk';

const client = new FactCheckerClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// Upload and process document
const document = await client.documents.upload(file);
const result = await client.documents.process(document.id);

// Fact-check text
const factCheck = await client.factCheck.text('The Earth is round');
```

---

**🎯 Complete API reference for building applications with the fact-checker platform**
