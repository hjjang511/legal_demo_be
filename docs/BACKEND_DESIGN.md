# Thiết Kế Backend - Hệ Thống Quản Lý Vụ Án AI

## 1. TỔNG QUAN HỆ THỐNG

### 1.1 Stack Công Nghệ Đề Xuất
- **Framework**: Node.js + Express.js hoặc NestJS
- **Database**: PostgreSQL (dữ liệu chính) + Redis (cache)
- **File Storage**: AWS S3 hoặc Azure Blob Storage
- **Message Queue**: RabbitMQ hoặc Apache Kafka (xử lý async)
- **Search**: Elasticsearch (tìm kiếm full-text)
- **Authentication**: JWT + OAuth2
- **AI/ML**: Python microservice cho OCR, NLP, tóm tắt

### 1.2 Kiến Trúc Tổng Quát
```
┌─────────────────┐
│   Next.js App   │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────────────────────────┐
│   API Gateway / Load Balancer       │
└────────┬────────────────────────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    ↓          ↓          ↓         ↓
┌────────┐ ┌───────┐ ┌─────────┐ ┌─────────┐
│  Auth  │ │ Cases │ │Documents│ │Messages │
│Service │ │Service│ │ Service │ │Service  │
└────────┘ └───────┘ └─────────┘ └─────────┘
    │          │          │         │
    └────┬─────┴──────────┴─────────┘
         │
    ┌────↓─────────────────────┐
    │     PostgreSQL DB        │
    │                          │
    │ ├─ users                 │
    │ ├─ cases                 │
    │ ├─ documents             │
    │ ├─ messages              │
    │ ├─ document_versions     │
    │ └─ audit_logs            │
    └──────────────────────────┘
    
    ┌──────────────────────────┐
    │   File Storage (S3)      │
    │                          │
    │ └─ /uploads/            │
    │   ├─ /cases/            │
    │   └─ /exports/          │
    └──────────────────────────┘

    ┌──────────────────────────┐
    │   Message Queue (RabbitMQ)
    │                          │
    │ ├─ document.upload       │
    │ ├─ document.process      │
    │ └─ brief.export          │
    └──────────────────────────┘

    ┌──────────────────────────┐
    │  AI Processing Service   │
    │   (Python Flask)         │
    │                          │
    │ ├─ OCR Processing        │
    │ ├─ Text Extraction       │
    │ ├─ Summarization         │
    │ └─ Embedding Generation  │
    └──────────────────────────┘
```

---

## 2. SCHEMA DATABASE

### 2.1 Bảng Users (Người Dùng)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  avatar_url VARCHAR(500),
  role ENUM('ADMIN', 'LAWYER', 'PARALEGAL', 'CLIENT') DEFAULT 'CLIENT',
  status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE',
  email_verified BOOLEAN DEFAULT FALSE,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

### 2.2 Bảng Cases (Vụ Án)
```sql
CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  case_number VARCHAR(100),
  case_type ENUM(
    'CIVIL', 'CRIMINAL', 'COMMERCIAL', 
    'LABOR', 'FAMILY', 'ADMINISTRATIVE', 'OTHER'
  ) DEFAULT 'CIVIL',
  court_name VARCHAR(255),
  judge_name VARCHAR(255),
  
  status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'CLOSED') DEFAULT 'PENDING',
  priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') DEFAULT 'MEDIUM',
  
  plaintiffs JSONB,  -- [{name, id, phone, email, role}]
  defendants JSONB,  -- [{name, id, phone, email, role}]
  lawyers JSONB,     -- [{name, id, bar_number, phone, email}]
  
  document_count INT DEFAULT 0,
  summary_status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
  summary_error_message TEXT,
  
  tags TEXT[] DEFAULT '{}',
  custom_fields JSONB,  -- {field_name: value}
  
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_cases_user_id ON cases(user_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);
CREATE INDEX idx_cases_case_number ON cases(case_number);
```

### 2.3 Bảng Documents (Tài Liệu)
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  file_name VARCHAR(500) NOT NULL,
  file_type VARCHAR(50) NOT NULL,  -- pdf, docx, txt, jpg, png, etc.
  file_size BIGINT NOT NULL,  -- bytes
  file_hash VARCHAR(64) UNIQUE,  -- SHA-256 for deduplication
  
  label ENUM(
    'ĐƠNN KHỞI KIỆN', 'PHÚC THẨM', 'BẰNG CHỨNG', 'HỢP ĐỒNG',
    'BIÊN BẢN', 'CHỨNG TỪ', 'BẢN ÁN', 'KHÁC'
  ) DEFAULT 'KHÁC',
  custom_label VARCHAR(255),
  
  file_url VARCHAR(500) NOT NULL,  -- S3 path
  preview_url VARCHAR(500),  -- Thumbnail or preview
  
  status ENUM('PENDING', 'UPLOADING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
  progress_percentage INT DEFAULT 0,
  
  -- OCR & Content Extraction
  raw_content TEXT,  -- Full extracted text from OCR
  content_summary TEXT,  -- AI generated summary
  page_count INT,
  language VARCHAR(10) DEFAULT 'vi',
  ocr_confidence FLOAT,  -- 0-1
  ocr_error_message TEXT,
  
  -- Embeddings for semantic search
  embedding_vector VECTOR(1536),  -- Or appropriate dimension
  
  -- Metadata
  extracted_entities JSONB,  -- {people: [], places: [], dates: []}
  key_terms TEXT[],
  metadata JSONB,  -- {created_date, author, subject, etc.}
  
  version INT DEFAULT 1,
  is_latest_version BOOLEAN DEFAULT TRUE,
  
  uploaded_by UUID NOT NULL REFERENCES users(id),
  uploaded_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_documents_case_id ON documents(case_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_label ON documents(label);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
```

### 2.4 Bảng Document Versions (Lịch Sử Tài Liệu)
```sql
CREATE TABLE document_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  version INT NOT NULL,
  file_url VARCHAR(500) NOT NULL,
  raw_content TEXT,
  changed_fields JSONB,  -- {field: {old_value, new_value}}
  changed_by UUID REFERENCES users(id),
  change_reason VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_doc_versions_document_id ON document_versions(document_id);
```

### 2.5 Bảng Case Summaries (Tóm Tắt Vụ Án)
```sql
CREATE TABLE case_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL UNIQUE REFERENCES cases(id) ON DELETE CASCADE,
  
  summary_sections JSONB,  -- [{title, content, citations: [{docId, fileName, page}]}]
  
  -- Sections content
  case_overview TEXT,
  legal_basis TEXT,
  analysis_evaluation TEXT,
  claims_and_demands TEXT,
  conclusion TEXT,
  
  status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
  error_message TEXT,
  
  generated_by VARCHAR(50),  -- 'SYSTEM' or user_id
  ai_model VARCHAR(100),  -- Model used for generation
  
  version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_case_summaries_case_id ON case_summaries(case_id);
```

### 2.6 Bảng Chat Messages (Tin Nhắn)
```sql
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  
  role ENUM('USER', 'BOT') NOT NULL,
  content TEXT NOT NULL,
  
  citations JSONB,  -- [{docId, fileName, content, page}]
  
  user_id UUID REFERENCES users(id),
  
  parent_message_id UUID REFERENCES chat_messages(id),  -- For thread
  
  search_context JSONB,  -- {documents_searched, keywords}
  relevance_score FLOAT,
  
  feedback ENUM('HELPFUL', 'NOT_HELPFUL', 'INCORRECT') DEFAULT NULL,
  
  created_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_messages_case_id ON chat_messages(case_id);
CREATE INDEX idx_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_messages_created_at ON chat_messages(created_at DESC);
```

### 2.7 Bảng Brief Exports (Tờ Trình)
```sql
CREATE TABLE brief_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  
  title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  
  export_format ENUM('DOCX', 'PDF', 'TXT', 'HTML') DEFAULT 'DOCX',
  file_url VARCHAR(500),  -- S3 path to generated file
  file_size BIGINT,
  
  template_used VARCHAR(100),
  customizations JSONB,  -- {section: modified_content}
  
  status ENUM('PENDING', 'GENERATING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
  error_message TEXT,
  
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_briefs_case_id ON brief_exports(case_id);
```

### 2.8 Bảng Audit Logs (Nhật Ký Kiểm Tra)
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  
  action VARCHAR(100) NOT NULL,  -- CREATE, UPDATE, DELETE, VIEW, EXPORT
  resource_type VARCHAR(50) NOT NULL,  -- CASE, DOCUMENT, MESSAGE
  resource_id UUID NOT NULL,
  
  changes JSONB,  -- {field: {old_value, new_value}}
  ip_address VARCHAR(45),
  user_agent TEXT,
  
  status ENUM('SUCCESS', 'FAILED') DEFAULT 'SUCCESS',
  error_message TEXT,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
```

### 2.9 Bảng Processing Jobs (Xử Lý Bất Đồng Bộ)
```sql
CREATE TABLE processing_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  job_type ENUM(
    'DOCUMENT_OCR', 
    'DOCUMENT_SUMMARIZATION',
    'CASE_SUMMARY_GENERATION',
    'BRIEF_GENERATION',
    'EMBEDDING_GENERATION'
  ) NOT NULL,
  
  resource_id UUID NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  
  status ENUM('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'RETRYING') DEFAULT 'QUEUED',
  
  priority INT DEFAULT 0,
  retry_count INT DEFAULT 0,
  max_retries INT DEFAULT 3,
  
  progress JSONB,  -- {percentage: 50, status: 'Processing page 5/10'}
  result JSONB,
  error_message TEXT,
  
  queue_name VARCHAR(100),  -- RabbitMQ queue
  message_id VARCHAR(255),  -- MQ message reference
  
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_resource ON processing_jobs(resource_type, resource_id);
CREATE INDEX idx_jobs_created_at ON processing_jobs(created_at DESC);
```

---

## 3. API ENDPOINTS

### 3.1 Authentication Endpoints

#### POST /api/auth/register
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "Nguyễn Văn A",
  "role": "LAWYER"
}
```
**Response:**
```json
{
  "success": true,
  "user": { "id", "email", "name", "role" },
  "token": "jwt_token",
  "refreshToken": "refresh_token"
}
```

#### POST /api/auth/login
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

#### POST /api/auth/refresh
Request with refreshToken cookie
```json
{
  "token": "new_jwt_token",
  "expiresIn": 3600
}
```

#### POST /api/auth/logout
Invalidate refresh token

---

### 3.2 Cases Endpoints

#### GET /api/cases
**Query params:**
- `page`: number (default: 1)
- `limit`: number (default: 10)
- `status`: PENDING|PROCESSING|COMPLETED|CLOSED
- `search`: string
- `sort`: createdAt|-createdAt|title|-title

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "string",
      "status": "COMPLETED",
      "documentCount": 8,
      "createdAt": "2024-03-15T10:30:00Z",
      "updatedAt": "2026-01-29T14:25:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5
  }
}
```

#### POST /api/cases
```json
{
  "title": "Tranh chấp hợp đồng mua bán bất động sản",
  "description": "Optional description",
  "caseType": "CIVIL",
  "courtName": "Tòa án nhân dân quận 1",
  "plaintiffs": [
    {
      "name": "Nguyễn Văn A",
      "phone": "0901234567",
      "email": "a@example.com"
    }
  ],
  "defendants": [
    {
      "name": "Công ty TNHH B",
      "phone": "0902345678",
      "email": "b@example.com"
    }
  ]
}
```

#### GET /api/cases/{caseId}
**Response with full details:**
```json
{
  "success": true,
  "data": {
    "id": "case-001",
    "title": "...",
    "status": "COMPLETED",
    "documents": [...],
    "summary": {...},
    "documentCount": 8,
    "createdAt": "...",
    "updatedAt": "..."
  }
}
```

#### PUT /api/cases/{caseId}
Update case details

#### DELETE /api/cases/{caseId}
Soft delete case

#### PATCH /api/cases/{caseId}/status
```json
{
  "status": "COMPLETED"
}
```

---

### 3.3 Documents Endpoints

#### POST /api/cases/{caseId}/documents/upload
**Multipart Form Data:**
```
file: [binary file]
label: "Hợp đồng"
customLabel: "Custom label (if label is 'Khác')"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "doc-uuid",
    "fileName": "contract.pdf",
    "label": "Hợp đồng",
    "status": "UPLOADING",
    "progress": 65,
    "fileUrl": "s3://bucket/cases/case-001/contract.pdf"
  }
}
```

#### GET /api/cases/{caseId}/documents
List all documents in case

#### GET /api/documents/{documentId}
Get document details with content

#### PUT /api/documents/{documentId}
```json
{
  "fileName": "New name",
  "label": "New label"
}
```

#### DELETE /api/documents/{documentId}
Soft delete document

#### GET /api/documents/{documentId}/download
Download original file

#### GET /api/documents/{documentId}/preview
Get preview/thumbnail

#### POST /api/documents/{documentId}/reprocess
Trigger reprocessing (OCR, summarization)

---

### 3.4 Case Summaries Endpoints

#### GET /api/cases/{caseId}/summary
Get case summary if available

#### POST /api/cases/{caseId}/summary/generate
Trigger summary generation (async)

**Response:**
```json
{
  "success": true,
  "jobId": "job-uuid",
  "status": "QUEUED",
  "message": "Case summary generation started"
}
```

#### GET /api/cases/{caseId}/summary/status
Check generation status

#### PUT /api/cases/{caseId}/summary
Update summary (manual edit)

---

### 3.5 Chat Endpoints

#### POST /api/cases/{caseId}/messages
```json
{
  "content": "Vấn đề tranh chấp là gì?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "msg-uuid",
    "role": "user",
    "content": "...",
    "timestamp": "2026-02-07T10:30:00Z"
  }
}
```

#### GET /api/cases/{caseId}/messages
Get all messages in conversation

#### DELETE /api/messages/{messageId}
Delete message

#### POST /api/messages/{messageId}/feedback
```json
{
  "feedback": "HELPFUL|NOT_HELPFUL|INCORRECT"
}
```

---

### 3.6 Brief Export Endpoints

#### POST /api/cases/{caseId}/brief/generate
```json
{
  "template": "default",
  "format": "DOCX",
  "customizations": {
    "section_name": "Custom content"
  }
}
```

**Response:**
```json
{
  "success": true,
  "jobId": "job-uuid",
  "status": "GENERATING",
  "estimatedTime": 30
}
```

#### GET /api/cases/{caseId}/brief/status/{jobId}
Check generation status

#### GET /api/briefs/{briefId}/download
Download generated brief

#### PUT /api/briefs/{briefId}
Edit brief content

---

### 3.7 Search Endpoints

#### GET /api/search/documents
Full-text document search

**Query params:**
- `q`: search query
- `caseId`: filter by case
- `label`: filter by document type
- `page`: pagination

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "documentId": "uuid",
      "fileName": "contract.pdf",
      "label": "Hợp đồng",
      "snippet": "...matching text...",
      "relevance": 0.95
    }
  ],
  "total": 25
}
```

---

### 3.8 Admin Endpoints

#### GET /api/admin/stats
System statistics

#### GET /api/admin/users
List users with filters

#### PUT /api/admin/users/{userId}/role
Change user role

#### GET /api/admin/audit-logs
View audit logs with filters

---

## 4. MESSAGE QUEUE - TASK PROCESSING

### 4.1 Document Upload Processing

```
Event: document.uploaded
├─ Task: extract_text_ocr
│  └─ Input: {documentId, fileUrl}
│  └─ Output: {rawContent, pageCount}
│
├─ Task: generate_embeddings
│  └─ Input: {documentId, content}
│  └─ Output: {embedding_vector}
│
├─ Task: extract_entities
│  └─ Input: {documentId, content}
│  └─ Output: {people, places, dates, organizations}
│
└─ Task: generate_summary
   └─ Input: {documentId, content}
   └─ Output: {summary}
```

### 4.2 Case Summary Generation

```
Event: case.summary_requested
├─ Task: collect_documents_content
├─ Task: synthesize_summary
├─ Task: generate_sections
└─ Task: create_citations
```

### 4.3 Brief Export Generation

```
Event: brief.export_requested
├─ Task: collect_case_data
├─ Task: apply_template
├─ Task: generate_document (DOCX/PDF)
└─ Task: upload_to_storage
```

---

## 5. ERROR HANDLING & STATUS CODES

### Common Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_DOCUMENT_FORMAT",
    "message": "User-friendly message",
    "details": { "validFormats": ["pdf", "docx"] }
  }
}
```

### HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Unique constraint violation |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Service down |

### Application Error Codes

```
AUTH_*
├─ INVALID_CREDENTIALS
├─ TOKEN_EXPIRED
├─ TOKEN_INVALID
└─ UNAUTHORIZED_ACCESS

DOCUMENT_*
├─ INVALID_FILE_FORMAT
├─ FILE_TOO_LARGE
├─ DUPLICATE_FILE
├─ UPLOAD_FAILED
└─ PROCESSING_FAILED

CASE_*
├─ CASE_NOT_FOUND
├─ CASE_ARCHIVED
└─ CASE_LOCKED

VALIDATION_*
├─ REQUIRED_FIELD_MISSING
├─ INVALID_EMAIL_FORMAT
└─ INVALID_PHONE_NUMBER

AI_*
├─ OCR_FAILED
├─ SUMMARIZATION_FAILED
├─ EMBEDDING_GENERATION_FAILED
└─ API_RATE_LIMIT_EXCEEDED
```

---

## 6. AUTHENTICATION & AUTHORIZATION

### 6.1 JWT Token Structure

**Access Token (expires in 1 hour):**
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "name": "Nguyễn Văn A",
  "role": "LAWYER",
  "permissions": ["read:cases", "write:cases", "read:documents"],
  "iat": 1707302400,
  "exp": 1707306000
}
```

**Refresh Token (expires in 7 days):**
```json
{
  "sub": "user_id",
  "type": "refresh",
  "iat": 1707302400,
  "exp": 1707907200
}
```

### 6.2 Role-Based Access Control (RBAC)

| Role | Permissions |
|------|------------|
| ADMIN | All permissions |
| LAWYER | Create/edit/delete own cases, manage documents, generate briefs |
| PARALEGAL | View/edit cases, upload documents, view summaries |
| CLIENT | View own cases, view documents, read summaries |

---

## 7. PERFORMANCE OPTIMIZATION

### 7.1 Caching Strategy

- **Redis Cache Layers:**
  - User sessions (TTL: 24 hours)
  - Case summaries (TTL: 7 days)
  - Document metadata (TTL: 24 hours)
  - Search results (TTL: 1 hour)
  - Frequently accessed documents (TTL: 3 days)

### 7.2 Database Optimization

- Connection pooling (Min: 10, Max: 50)
- Query optimization with proper indexes
- Pagination for large datasets (default limit: 10-50)
- Soft deletes to preserve data integrity

### 7.3 File Storage Optimization

- Multipart upload for large files (>100MB)
- File compression before storage
- CDN for document preview/download
- Automatic old file cleanup (configurable retention)

### 7.4 API Rate Limiting

```
Standard User: 1000 requests/hour
Premium User: 10000 requests/hour
Bot/Service Account: Custom limits
```

---

## 8. SECURITY MEASURES

### 8.1 Input Validation

- Sanitize all user inputs
- File upload validation (type, size, virus scan)
- SQL injection prevention (prepared statements)
- XSS protection (output encoding)

### 8.2 Data Protection

- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- PII masking in logs
- Regular security audits

### 8.3 Access Control

- JWT-based authentication
- API key for service-to-service communication
- Audit logging for all sensitive operations
- IP whitelisting for admin endpoints

---

## 9. MONITORING & LOGGING

### 9.1 Logging Strategy

- **Application Logs**: All API requests, errors, warnings
- **Audit Logs**: User actions, data changes
- **Performance Logs**: Processing times, slow queries
- **Security Logs**: Authentication attempts, unauthorized access

**Log Format:**
```json
{
  "timestamp": "2026-02-07T10:30:00Z",
  "level": "INFO",
  "service": "cases-api",
  "message": "Case created successfully",
  "userId": "user-uuid",
  "caseId": "case-uuid",
  "duration_ms": 245,
  "traceId": "unique-trace-id"
}
```

### 9.2 Monitoring Metrics

- API response times (p50, p95, p99)
- Error rate and error types
- Document processing success rate
- Active users and concurrent requests
- Queue length and processing time
- Database query performance
- File storage usage

### 9.3 Alerts

- High error rate (>1%)
- API response time > 1000ms
- Queue backlog > 100 items
- AI service unavailable
- Database connection pool exhausted
- Storage quota near limit

---

## 10. DEPLOYMENT & SCALABILITY

### 10.1 Microservices Architecture

```
├─ API Gateway (Port 3000)
├─ Auth Service (Port 3001)
├─ Cases Service (Port 3002)
├─ Documents Service (Port 3003)
├─ Chat Service (Port 3004)
├─ AI Processing Service (Python, Port 5000)
└─ Background Jobs Service
```

### 10.2 Horizontal Scaling

- Stateless API services (can run multiple instances)
- Load balancer (Nginx/HAProxy)
- Database read replicas for reporting
- Separate processing workers for background jobs

### 10.3 Container Deployment

```dockerfile
# Example Dockerfile structure
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Docker Compose for local development**
**Kubernetes for production**

---

## 11. ENVIRONMENT VARIABLES

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legal_demo
DB_USER=postgres
DB_PASSWORD=securePassword

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT
JWT_SECRET=your-secret-key-min-32-chars
JWT_EXPIRES_IN=3600
REFRESH_TOKEN_SECRET=refresh-secret
REFRESH_TOKEN_EXPIRES_IN=604800

# File Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=legal-demo-bucket
S3_BASE_URL=https://bucket.s3.amazonaws.com

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# AI Services
AI_SERVICE_URL=http://localhost:5000
AI_SERVICE_TIMEOUT=300000

# Security
CORS_ORIGIN=http://localhost:3000
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_MAX_REQUESTS=1000

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

---

## 12. API VERSIONING STRATEGY

```
/api/v1/cases   (current version)
/api/v2/cases   (future version)
```

Support previous version for 6 months before deprecation.

---

## 13. DEVELOPMENT WORKFLOW

### Initial Setup
```bash
npm install
cp .env.example .env
npm run db:migrate
npm run db:seed
npm run dev
```

### Database Migrations
```bash
# Create migration
npm run db:migration:create add_new_table

# Run migrations
npm run db:migrate

# Revert migration
npm run db:rollback
```

---

## 14. TESTING STRATEGY

- **Unit Tests**: Service layer logic (Jest)
- **Integration Tests**: API endpoints (Supertest)
- **E2E Tests**: Full user workflows (Cypress/Playwright)
- **Load Tests**: Performance under stress (k6/JMeter)
- **Security Tests**: OWASP Top 10 (ZAAP/Burp)

**Test Coverage Target: ≥80%**

