# API Specifications - Chi Tiết Endpoints

## REQUEST/RESPONSE EXAMPLES

### 1. Cases Management API

#### 1.1 Create Case
**Endpoint:** `POST /api/v1/cases`

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/cases \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tranh chấp hợp đồng mua bán bất động sản - Nguyễn Văn A vs Công ty TNHH B",
    "description": "Vụ việc gồm 3 bên: nguyên đơn, bị đơn và người trung gian",
    "caseType": "CIVIL",
    "courtName": "Tòa án nhân dân quận 1, TP. Hồ Chí Minh",
    "caseNumber": "01/2024/KDTM-ST",
    "judge_name": "Phạm Thị Minh",
    "priority": "HIGH",
    "plaintiffs": [
      {
        "name": "Nguyễn Văn A",
        "phone": "0901234567",
        "email": "a@example.com",
        "id_number": "000123456789"
      }
    ],
    "defendants": [
      {
        "name": "Công ty TNHH B",
        "phone": "0902345678",
        "email": "contact@b.com",
        "tax_id": "0123456789"
      }
    ],
    "lawyers": [
      {
        "name": "Luật sư Trần Văn C",
        "phone": "0903456789",
        "email": "c@lawfirm.com",
        "bar_number": "LAW123456"
      }
    ]
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Case created successfully",
  "data": {
    "id": "case-550e8400-e29b-41d4-a716-446655440000",
    "title": "Tranh chấp hợp đồng mua bán bất động sản - Nguyễn Văn A vs Công ty TNHH B",
    "description": "Vụ việc gồm 3 bên: nguyên đơn, bị đơn và người trung gian",
    "caseType": "CIVIL",
    "status": "PENDING",
    "priority": "HIGH",
    "documentCount": 0,
    "summaryStatus": "PENDING",
    "createdBy": "user-123",
    "createdAt": "2026-02-07T10:30:00.000Z",
    "updatedAt": "2026-02-07T10:30:00.000Z",
    "courtName": "Tòa án nhân dân quận 1, TP. Hồ Chí Minh",
    "caseNumber": "01/2024/KDTM-ST",
    "judgeName": "Phạm Thị Minh"
  }
}
```

**Possible Errors:**
```json
// 400 Bad Request - Missing required fields
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing or invalid required fields",
    "details": {
      "title": "Title is required",
      "plaintiffs": "At least one plaintiff is required"
    }
  }
}

// 401 Unauthorized
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}

// 409 Conflict - Duplicate case
{
  "success": false,
  "error": {
    "code": "CASE_ALREADY_EXISTS",
    "message": "A case with this case number already exists",
    "details": {
      "existingCaseId": "case-123"
    }
  }
}
```

---

#### 1.2 Get Cases List
**Endpoint:** `GET /api/v1/cases`

**Request:**
```bash
curl -X GET "http://localhost:3000/api/v1/cases?page=1&limit=10&status=COMPLETED&sort=-createdAt&search=hợp%20đồng" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Query Parameters:**
| Parameter | Type | Default | Example |
|-----------|------|---------|---------|
| page | integer | 1 | 1 |
| limit | integer | 10 | 20 |
| status | string | - | PENDING,PROCESSING,COMPLETED,CLOSED |
| priority | string | - | LOW,MEDIUM,HIGH,URGENT |
| search | string | - | "hợp đồng" |
| sort | string | -updatedAt | createdAt, -title |
| startDate | string | - | 2026-01-01 |
| endDate | string | - | 2026-02-07 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Cases retrieved successfully",
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5,
    "hasNextPage": true,
    "hasPrevPage": false
  },
  "data": [
    {
      "id": "case-001",
      "title": "Tranh chấp hợp đồng mua bán bất động sản - Nguyễn Văn A vs Công ty TNHH B",
      "caseType": "CIVIL",
      "status": "COMPLETED",
      "priority": "HIGH",
      "caseNumber": "01/2024/KDTM-ST",
      "documentCount": 8,
      "summaryStatus": "COMPLETED",
      "courName": "Tòa án nhân dân quận 1",
      "createdAt": "2024-03-15T10:30:00.000Z",
      "updatedAt": "2026-01-29T14:25:00.000Z",
      "tags": ["bất động sản", "mua bán", "2024"]
    },
    {
      "id": "case-002",
      "title": "Tranh chấp lao động - Trần Thị C kiện Công ty D",
      "caseType": "LABOR",
      "status": "PROCESSING",
      "priority": "MEDIUM",
      "caseNumber": "02/2024/LD-ST",
      "documentCount": 5,
      "summaryStatus": "PROCESSING",
      "courtName": "Tòa án nhân dân quận 1",
      "createdAt": "2024-11-01T08:15:00.000Z",
      "updatedAt": "2026-01-28T16:45:00.000Z",
      "tags": ["lao động", "tranh chấp"]
    }
  ]
}
```

---

#### 1.3 Get Case Details
**Endpoint:** `GET /api/v1/cases/{caseId}`

**Request:**
```bash
curl -X GET http://localhost:3000/api/v1/cases/case-001 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Case details retrieved",
  "data": {
    "id": "case-001",
    "title": "Tranh chấp hợp đồng mua bán bất động sản...",
    "description": "Chi tiết vụ án...",
    "caseType": "CIVIL",
    "status": "COMPLETED",
    "priority": "HIGH",
    "caseNumber": "01/2024/KDTM-ST",
    "courNumber": "Tòa án nhân dân quận 1, TP. Hồ Chí Minh",
    "judgeName": "Phạm Thị Minh",
    "documentCount": 8,
    "summaryStatus": "COMPLETED",
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
    ],
    "lawyers": [
      {
        "name": "Luật sư Trần Văn C",
        "barNumber": "LAW123456",
        "phone": "0903456789"
      }
    ],
    "customFields": {
      "settlement_date": "2025-12-15",
      "compensation_amount": "2500000000"
    },
    "tags": ["bất động sản", "2024"],
    "createdBy": "user-123",
    "createdAt": "2024-03-15T10:30:00.000Z",
    "updatedAt": "2026-01-29T14:25:00.000Z",
    "summary": {
      "id": "summary-001",
      "status": "COMPLETED",
      "sections": [
        {
          "title": "I. SƠ LƯỢC VỤ VIỆC",
          "content": "Nguyên đơn Nguyễn Văn A ký hợp đồng mua bán bất động sản...",
          "citations": [
            {
              "docId": "doc-001",
              "fileName": "hợp_đồng.pdf",
              "page": 1
            }
          ]
        }
      ],
      "createdAt": "2026-01-20T09:15:00.000Z"
    },
    "documents": [
      {
        "id": "doc-001",
        "fileName": "hợp_đồng.pdf",
        "label": "Hợp đồng",
        "status": "COMPLETED",
        "pageCount": 5,
        "uploadedAt": "2026-01-15T10:30:00.000Z"
      }
    ]
  }
}
```

---

### 2. Documents Management API

#### 2.1 Upload Document
**Endpoint:** `POST /api/v1/cases/{caseId}/documents/upload`

**Request (Multipart Form Data):**
```bash
curl -X POST http://localhost:3000/api/v1/cases/case-001/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/contract.pdf" \
  -F "label=Hợp đồng" \
  -F "customLabel=" \
  -F "tags=contract,2024"
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Document uploaded successfully",
  "data": {
    "id": "doc-550e8400-e29b-41d4-a716-446655440001",
    "caseId": "case-001",
    "fileName": "contract.pdf",
    "fileType": "pdf",
    "fileSize": 2457600,
    "label": "Hợp đồng",
    "status": "UPLOADING",
    "progress": 100,
    "fileUrl": "s3://legal-demo-bucket/cases/case-001/doc-001/contract.pdf",
    "uploadedAt": "2026-02-07T10:35:00.000Z",
    "uploadedBy": "user-123"
  }
}
```

**Note:** Document will automatically transition through states:
- UPLOADING → PROCESSING → COMPLETED (or FAILED)

---

#### 2.2 Get Document Details
**Endpoint:** `GET /api/v1/documents/{documentId}`

**Request:**
```bash
curl -X GET http://localhost:3000/api/v1/documents/doc-001 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Document retrieved",
  "data": {
    "id": "doc-001",
    "caseId": "case-001",
    "fileName": "hợp_đồng.pdf",
    "fileType": "pdf",
    "fileSize": 2457600,
    "label": "Hợp đồng",
    "status": "COMPLETED",
    "progress": 100,
    "fileUrl": "s3://legal-demo-bucket/cases/case-001/doc-001/contract.pdf",
    "previewUrl": "s3://legal-demo-bucket/cases/case-001/doc-001/contract-thumb.jpg",
    "pageCount": 5,
    "language": "vi",
    "ocrConfidence": 0.92,
    "rawContent": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM...",
    "summary": "Hợp đồng mua bán bất động sản giữa Nguyễn Văn A và Công ty TNHH B...",
    "entities": {
      "people": ["Nguyễn Văn A", "Trần Thị B"],
      "organizations": ["Công ty TNHH B", "Ngân hàng A"],
      "locations": ["Quận 1, TP. Hồ Chí Minh", "Lô 5, Phường 1"],
      "dates": ["15/03/2024", "30/09/2024"],
      "money": ["3.5 tỷ đồng", "2.45 tỷ đồng"]
    },
    "keyTerms": ["hợp đồng", "mua bán", "bất động sản", "thanh toán", "bàn giao"],
    "metadata": {
      "created_date": "2024-03-15",
      "author": "Luật sư Nguyễn Văn A",
      "subject": "Hợp đồng mua bán bất động sản"
    },
    "uploadedBy": "user-123",
    "uploadedAt": "2026-01-15T10:30:00.000Z",
    "processedAt": "2026-01-15T10:35:00.000Z",
    "updatedAt": "2026-01-29T14:25:00.000Z"
  }
}
```

---

#### 2.3 Edit Document
**Endpoint:** `PUT /api/v1/documents/{documentId}`

**Request:**
```bash
curl -X PUT http://localhost:3000/api/v1/documents/doc-001 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "Hợp_đồng_mua_bán_bất_động_sản.pdf",
    "label": "Hợp đồng",
    "summary": "Custom summary if needed"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": "doc-001",
    "fileName": "Hợp_đồng_mua_bán_bất_động_sản.pdf",
    "label": "Hợp đồng",
    "updatedAt": "2026-02-07T11:00:00.000Z"
  }
}
```

---

#### 2.4 Delete Document  
**Endpoint:** `DELETE /api/v1/documents/{documentId}`

**Request:**
```bash
curl -X DELETE http://localhost:3000/api/v1/documents/doc-001 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "data": {
    "id": "doc-001",
    "deletedAt": "2026-02-07T11:05:00.000Z"
  }
}
```

---

### 3. Chat Interface API

#### 3.1 Send Message
**Endpoint:** `POST /api/v1/cases/{caseId}/messages`

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/cases/case-001/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Vấn đề tranh chấp chính trong vụ này là gì?"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Message sent",
  "data": {
    "id": "msg-123",
    "caseId": "case-001",
    "role": "user",
    "content": "Vấn đề tranh chấp chính trong vụ này là gì?",
    "userId": "user-123",
    "timestamp": "2026-02-07T11:10:00.000Z"
  },
  "processing": {
    "status": "PROCESSING",
    "estimatedTime": 2
  }
}

// After processing (WebSocket or polling):
{
  "success": true,
  "data": {
    "id": "msg-124",
    "caseId": "case-001",
    "role": "bot",
    "content": "Vấn đề tranh chấp chính là: Bị đơn không thực hiện nghĩa vụ bàn giao căn hộ...",
    "citations": [
      {
        "docId": "doc-001",
        "fileName": "hợp_đồng.pdf",
        "content": "Thời hạn bàn giao là 30/09/2024",
        "page": 2
      }
    ],
    "searchContext": {
      "documentsSearched": 8,
      "keywords": ["tranh chấp", "bàn giao"],
      "relevanceScore": 0.89
    },
    "timestamp": "2026-02-07T11:10:02.500Z"
  }
}
```

---

#### 3.2 Get Chat History
**Endpoint:** `GET /api/v1/cases/{caseId}/messages`

**Request:**
```bash
curl -X GET "http://localhost:3000/api/v1/cases/case-001/messages?page=1&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Messages retrieved",
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 25
  },
  "data": [
    {
      "id": "msg-122",
      "role": "bot",
      "content": "Xin chào! Tôi sẽ giúp bạn phân tích vụ án này...",
      "timestamp": "2026-02-07T10:30:00.000Z"
    },
    {
      "id": "msg-123",
      "role": "user",
      "content": "Vấn đề tranh chấp chính là gì?",
      "timestamp": "2026-02-07T11:10:00.000Z"
    },
    {
      "id": "msg-124",
      "role": "bot",
      "content": "Vấn đề tranh chấp chính là...",
      "citations": [
        {
          "docId": "doc-001",
          "fileName": "hợp_đồng.pdf",
          "page": 2
        }
      ],
      "timestamp": "2026-02-07T11:10:02.500Z"
    }
  ]
}
```

---

### 4. Case Summary API

#### 4.1 Generate Summary
**Endpoint:** `POST /api/v1/cases/{caseId}/summary/generate`

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/cases/case-001/summary/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "includeDocuments": true,
    "sections": ["overview", "legal_basis", "analysis", "conclusion"]
  }'
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Summary generation started",
  "data": {
    "jobId": "job-550e8400-e29b-41d4-a716-446655440002",
    "status": "QUEUED",
    "caseId": "case-001",
    "estimatedTime": 30
  }
}
```

To check status:
```bash
curl -X GET http://localhost:3000/api/v1/cases/case-001/summary/status/job-550e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response when COMPLETED:**
```json
{
  "success": true,
  "message": "Summary generation completed",
  "data": {
    "id": "summary-001",
    "caseId": "case-001",
    "status": "COMPLETED",
    "summaryections": [
      {
        "title": "I. SƠ LƯỢC VỤ VIỆC",
        "content": "Ngày 15/03/2024, nguyên đơn Nguyễn Văn A đã ký hợp đồng mua bán bất động sản...",
        "citations": [
          {
            "docId": "doc-001",
            "fileName": "hợp_đồng.pdf",
            "page": 1
          }
        ]
      },
      {
        "title": "II. CƠ SỞ PHÁP LÝ",
        "content": "1. Luật Dân sự năm 2015\n   - Điều 405: Hợp đồng mua bán tài sản\n   - Điều 427: Trách nhiệm của bên bán\n\n2. Luật Kinh doanh bất động sản năm 2014...",
        "citations": [
          {
            "docId": "doc-003",
            "fileName": "luật_dân_sự.pdf",
            "page": 15
          }
        ]
      }
    ],
    "generatedAt": "2026-02-07T11:35:00.000Z"
  }
}
```

---

### 5. Brief Export API

#### 5.1 Generate Brief
**Endpoint:** `POST /api/v1/cases/{caseId}/brief/generate`

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/cases/case-001/brief/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "default",
    "format": "DOCX",
    "title": "TỜ TRÌNH về việc: Tranh chấp hợp đồng mua bán...",
    "customizations": {
      "case_overview": "Custom content here...",
      "conclusion": "Modified conclusion..."
    }
  }'
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Brief generation started",
  "data": {
    "jobId": "job-550e8400-e29b-41d4-a716-446655440003",
    "status": "GENERATING",
    "caseId": "case-001",
    "expectedDuration": 15
  }
}
```

Check status:
```bash
curl -X GET http://localhost:3000/api/v1/cases/case-001/brief/status/job-550e8400-e29b-41d4-a716-446655440003 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Download when ready:
```bash
curl -X GET http://localhost:3000/api/v1/briefs/brief-001/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -O -J  # Save with original filename
```

---

## ERROR CODES REFERENCE

| Error Code | HTTP Status | Description | Example |
|------------|-------------|-------------|---------|
| INVALID_CREDENTIALS | 401 | Wrong email or password | Login failed |
| TOKEN_EXPIRED | 401 | JWT token has expired | Refresh needed |
| TOKEN_INVALID | 401 | Invalid or malformed token | Bad token format |
| UNAUTHORIZED_ACCESS | 403 | No permission for resource | User can't access case |
| VALIDATION_ERROR | 400 | Input validation failed | Missing fields |
| INVALID_FILE_FORMAT | 400 | Unsupported file type | Only PDF, DOCX allowed |
| FILE_TOO_LARGE | 413 | File exceeds max size (500MB) | Upload failed |
| DUPLICATE_FILE | 409 | File already uploaded | MD5 hash collision |
| CASE_NOT_FOUND | 404 | Case doesn't exist | Invalid case ID |
| DOCUMENT_NOT_FOUND | 404 | Document doesn't exist | Invalid doc ID |
| CASE_ARCHIVED | 400 | Cannot modify archived case | Case is closed |
| OCR_FAILED | 500 | OCR processing failed | Bad PDF quality |
| SUMMARIZATION_FAILED | 500 | AI summary generation failed | API timeout |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Wait before retry |
| DATABASE_ERROR | 500 | Database operation failed | Server error |
| SERVICE_UNAVAILABLE | 503 | Backend service down | Try again later |

---

## Rate Limiting

All endpoints use sliding window rate limiting:

**Standard Users:**
- 1000 requests/hour
- 100 requests/minute

**Premium Users:**
- 10000 requests/hour
- 500 requests/minute

**Response Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1707306000
```

When limit exceeded:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retryAfter": 3600
  }
}
```

