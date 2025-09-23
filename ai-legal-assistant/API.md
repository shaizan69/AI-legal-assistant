# AI Legal Assistant - API Documentation

This document provides comprehensive API documentation for the AI Legal Assistant backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Full Name",
  "company": "Company Name",
  "role": "Role"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "is_verified": false,
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### Login User
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### Update User
```http
PUT /api/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "company": "Updated Company"
}
```

### Document Management

#### Upload Document
```http
POST /api/upload/
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
title: "Document Title"
document_type: "contract"
description: "Document description"
```

**Response:**
```json
{
  "id": 1,
  "filename": "document_123.pdf",
  "original_filename": "contract.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "word_count": 5000,
  "character_count": 25000,
  "document_type": "contract",
  "title": "Document Title",
  "is_processed": false,
  "processing_status": "pending",
  "created_at": "2023-01-01T00:00:00Z",
  "owner_id": 1
}
```

#### Get Documents
```http
GET /api/upload/
Authorization: Bearer <token>
Query Parameters:
  - page: 1 (default)
  - size: 10 (default)
  - document_type: "contract" (optional)
  - search: "search term" (optional)
```

**Response:**
```json
{
  "documents": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

#### Get Document
```http
GET /api/upload/{document_id}
Authorization: Bearer <token>
```

#### Delete Document
```http
DELETE /api/upload/{document_id}
Authorization: Bearer <token>
```

### Document Analysis

#### Generate Summary
```http
POST /api/summarize/
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": 1,
  "summary_type": "comprehensive",
  "include_risks": true,
  "include_obligations": true,
  "include_financial_terms": true
}
```

**Response:**
```json
{
  "document_id": 1,
  "summary": "This contract is between...",
  "structured_summary": {
    "overview": "Contract overview...",
    "key_terms": ["Term 1", "Term 2"],
    "important_dates": ["2023-12-31"],
    "financial_terms": ["$10,000 payment"],
    "obligations": ["Party A must...", "Party B must..."],
    "termination": "Contract terminates on...",
    "risk_factors": ["Risk 1", "Risk 2"]
  },
  "word_count": 5000,
  "analysis_date": "2023-01-01T00:00:00Z",
  "confidence_score": 0.85,
  "processing_time": 2.5
}
```

#### Get Summary
```http
GET /api/summarize/{document_id}
Authorization: Bearer <token>
```

#### Detect Risks
```http
POST /api/risks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": 1,
  "risk_types": ["auto_renewal", "unlimited_liability"],
  "min_confidence": 0.5
}
```

**Response:**
```json
{
  "document_id": 1,
  "risks": [
    {
      "id": 1,
      "risk_level": "High",
      "risk_type": "auto_renewal",
      "description": "Contract automatically renews unless terminated",
      "location": "Section 5.2",
      "recommendation": "Add explicit termination clause",
      "severity_score": 0.8,
      "likelihood_score": 0.9,
      "overall_score": 0.85,
      "clause_reference": "5.2",
      "page_number": 3,
      "line_number": 45,
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "summary": {
    "total_risks": 1,
    "high_risks": 1,
    "medium_risks": 0,
    "low_risks": 0,
    "risk_types": {"auto_renewal": 1},
    "overall_risk_score": 0.85,
    "recommendations": ["Add explicit termination clause"]
  },
  "processing_time": 1.2
}
```

#### Get Risks
```http
GET /api/risks/{document_id}
Authorization: Bearer <token>
```

### Document Comparison

#### Compare Documents
```http
POST /api/compare/
Authorization: Bearer <token>
Content-Type: application/json

{
  "document1_id": 1,
  "document2_id": 2,
  "comparison_name": "Contract Comparison",
  "comparison_type": "custom"
}
```

**Response:**
```json
{
  "id": 1,
  "comparison_name": "Contract Comparison",
  "summary": "The two contracts differ in...",
  "key_differences": [
    {
      "section": "Payment Terms",
      "document1": "Payment due in 30 days",
      "document2": "Payment due in 60 days"
    }
  ],
  "similarities": [
    {
      "section": "Termination",
      "description": "Both contracts have 30-day termination notice"
    }
  ],
  "recommendations": [
    "Consider standardizing payment terms",
    "Review termination clauses for consistency"
  ],
  "comparison_type": "custom",
  "similarity_score": 0.75,
  "processing_time": 3.2,
  "created_at": "2023-01-01T00:00:00Z",
  "user_id": 1,
  "document1_id": 1,
  "document2_id": 2
}
```

#### Get Comparison
```http
GET /api/compare/{comparison_id}
Authorization: Bearer <token>
```

#### Get All Comparisons
```http
GET /api/compare/
Authorization: Bearer <token>
```

### Q&A Sessions

#### Create Q&A Session
```http
POST /api/qa/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": 1,
  "session_name": "Contract Q&A"
}
```

**Response:**
```json
{
  "id": 1,
  "session_name": "Contract Q&A",
  "is_active": true,
  "total_questions": 0,
  "created_at": "2023-01-01T00:00:00Z",
  "user_id": 1,
  "document_id": 1
}
```

#### Ask Question
```http
POST /api/qa/ask
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What is the payment schedule?",
  "session_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "question": "What is the payment schedule?",
  "answer": "According to Section 3.2, payments are due within 30 days of invoice receipt...",
  "confidence_score": 0.92,
  "context_used": "Section 3.2 of the contract states...",
  "sources": [
    {
      "section": "3.2",
      "content": "Payment Terms: All invoices shall be paid within 30 days...",
      "relevance_score": 0.95
    }
  ],
  "processing_time": 1.5,
  "model_used": "gpt-3.5-turbo",
  "created_at": "2023-01-01T00:00:00Z",
  "answered_at": "2023-01-01T00:00:01Z",
  "session_id": 1
}
```

#### Get Session Questions
```http
GET /api/qa/sessions/{session_id}/questions
Authorization: Bearer <token>
```

#### Provide Feedback
```http
PUT /api/qa/questions/{question_id}/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_helpful": true,
  "rating": 5,
  "feedback": "Very helpful answer"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "status_code": 400,
  "path": "/api/endpoint"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Validation Errors
```json
{
  "error": "Validation error",
  "status_code": 422,
  "path": "/api/endpoint",
  "details": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

## Rate Limiting

- **API Endpoints**: 10 requests per second per IP
- **Upload Endpoints**: 1 request per second per IP
- **Q&A Endpoints**: 5 requests per second per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

## File Upload Limits

- **Maximum file size**: 10MB
- **Allowed file types**: PDF, DOCX, DOC
- **Maximum files per user**: 1000

## Pagination

List endpoints support pagination with these query parameters:

- `page`: Page number (default: 1)
- `size`: Items per page (default: 10, max: 100)

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

## Webhooks

The API supports webhooks for document processing events:

### Webhook Events

- `document.uploaded` - Document uploaded
- `document.processed` - Document processing completed
- `document.failed` - Document processing failed
- `analysis.completed` - Analysis completed
- `risk.detected` - Risk analysis completed

### Webhook Payload
```json
{
  "event": "document.processed",
  "timestamp": "2023-01-01T00:00:00Z",
  "data": {
    "document_id": 1,
    "user_id": 1,
    "processing_time": 2.5,
    "status": "completed"
  }
}
```

## SDKs and Libraries

### Python
```python
import requests

# Initialize client
base_url = "http://localhost:8000"
headers = {"Authorization": f"Bearer {token}"}

# Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {"title": "My Document"}
    response = requests.post(f"{base_url}/api/upload/", files=files, data=data, headers=headers)
```

### JavaScript
```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'My Document');

const response = await fetch('/api/upload/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

### cURL Examples

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Upload document
curl -X POST "http://localhost:8000/api/upload/" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "title=My Document"

# Ask question
curl -X POST "http://localhost:8000/api/qa/ask" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the payment schedule?", "session_id": 1}'
```

## Interactive API Documentation

Visit `/docs` for interactive Swagger UI documentation:
- **Development**: http://localhost:8000/docs
- **Production**: https://your-domain.com/docs

Alternative ReDoc documentation available at `/redoc`.
