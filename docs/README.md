# Backend Design Documentation - Hệ Thống Quản Lý Vụ Án AI

## 📋 Tổng Quan

Bộ tài liệu này cung cấp thiết kế backend chi tiết cho hệ thống quản lý vụ án được hỗ trợ bởi AI. Hệ thống này cho phép:

✅ Tạo và quản lý hồ sơ vụ án  
✅ Upload và xử lý tài liệu pháp lý  
✅ Tự động trích xuất thông tin từ tài liệu bằng AI (OCR, NLP)  
✅ Tìm kiếm ngữ nghĩa trong tài liệu  
✅ Hỏi đáp thông minh qua chatbot AI  
✅ Tự động tạo tờ trình/kiến nghị  

---

## 📚 Tài Liệu Thiết Kế

### 1. **BACKEND_DESIGN.md** - Thiết Kế Hệ Thống Toàn Bộ
   - **Stack công nghệ**: Node.js, Express, PostgreSQL, Redis, RabbitMQ
   - **Kiến trúc tổng quát**: Microservices, message queue, worker pattern
   - **Database schema**: 9 bảng chính với đầy đủ relationships
   - **API endpoints**: 50+ endpoints với request/response examples
   - **Authentication & Authorization**: JWT-based RBAC
   - **Error handling**: Comprehensive error codes
   - **Performance optimization**: Caching, indexing, rate limiting
   - **Security measures**: Encryption, validation, audit logging

### 2. **AI_PIPELINE.md** - Quy Trình Xử Lý AI/ML
   - **Document processing pipeline**: OCR → NLP → Summarization → Embeddings
   - **OCR service**: Xử lý PDF, images, DOCX with Tesseract & PyTorch
   - **NLP service**: Trích xuất entities, key terms, Vietnamese/English
   - **Summarization**: Extractive & Abstractive summarization
   - **Embedding service**: Vector embeddings cho semantic search
   - **Message queue integration**: RabbitMQ consumer/producer pattern
   - **Detailed code examples**: Sử dụng Python với Tesseract, SpaCy, Transformers

### 3. **API_SPECIFICATIONS.md** - Chi Tiết Endpoints & Examples
   - **Authentication API**: Register, Login, Token refresh
   - **Cases API**: CRUD operations, status management
   - **Documents API**: Upload, edit, delete, download
   - **Chat API**: Send messages, retrieve history, citations
   - **Summary API**: Generate, retrieve, update summaries
   - **Brief Export API**: Generate briefs in DOCX/PDF format
   - **Search API**: Full-text document search
   - **Error responses**: Chi tiết các error codes
   - **Rate limiting**: Moạn tính toánolling strategies
   - **cURL examples**: Mọi endpoint đều có ví dụ cụ thể

### 4. **DEPLOYMENT_GUIDE.md** - Hướng Dẫn Deploy & Infra
   - **Local development**: Docker Compose setup (7 services)
   - **Project structure**: Layout cho API, Worker, AI Service
   - **Dockerfile examples**: Multi-stage builds, optimizations
   - **Kubernetes manifests**: Deployments, Statefulsets, Services
   - **CI/CD pipeline**: GitHub Actions workflow
   - **Environment variables**: Configuration management
   - **Database migrations**: Schema management
   - **Monitoring**: Prometheus, ELK Stack configuration

### 5. **IMPLEMENTATION_ROADMAP.md** - Kế Hoạch Phát Triển
   - **4 Phase plan**: MVP → AI Integration → Chat → Advanced Features
   - **12-week timeline**: Chi tiết công việc từng tuần
   - **Technology details**: Code templates và setup instructions
   - **Priority matrix**: High/Medium priority tasks
   - **Testing strategy**: Unit, Integration, E2E tests
   - **KPIs & metrics**: Success criteria
   - **Resource requirements**: Team, Infrastructure

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────┐
│     Frontend (Next.js/React)        │
│     (Đã tồn tại)                    │
└────────────────┬────────────────────┘
                 │ HTTP/REST
                 ↓
┌─────────────────────────────────────┐
│         API Gateway (Nginx)         │
└────────────────┬────────────────────┘
         ┌───────┴────────┬──────────────┬──────────────┐
         ↓                ↓              ↓              ↓
    ┌─────────┐      ┌─────────┐   ┌─────────┐   ┌──────────┐
    │  Auth   │      │ Cases   │   │Documents│   │ Messages │
    │Service  │      │ Service │   │ Service │   │ Service  │
    └─────────┘      └─────────┘   └─────────┘   └──────────┘
         └──────────────┬──────────────┬──────────────┘
                        ↓
                ┌──────────────────┐
                │  PostgreSQL DB   │
                │  (Case, Docs,    │
                │   Messages, etc) │
                └──────────────────┘

        ┌──────────────────┐
        │  Redis Cache     │
        │  (Sessions,      │
        │   Cache layers)  │
        └──────────────────┘

        ┌──────────────────┐
        │  RabbitMQ        │
        │  Message Queue   │
        └────────┬─────────┘
                 ↓
        ┌──────────────────┐
        │ Worker Service   │
        │ (Node.js)        │
        └────────┬─────────┘
                 ↓
        ┌──────────────────┐
        │  AI Service      │
        │  (Python)        │
        │  - OCR           │
        │  - NLP           │
        │  - Summarization │
        │  - Embeddings    │
        └──────────────────┘

        ┌──────────────────┐
        │  S3 Storage      │
        │  (Documents)     │
        └──────────────────┘

        ┌──────────────────┐
        │  Elasticsearch   │
        │  (Full-text)     │
        └──────────────────┘
```

---

## 🚀 Quick Start

### 1. Development Setup
```bash
# Clone repository
git clone <repo-url>
cd legal_demo

# Start all services with Docker Compose
docker-compose up -d

# Services will be available at:
# - API: http://localhost:3000
# - RabbitMQ UI: http://localhost:15672
# - Elasticsearch: http://localhost:9200
# - PostgreSQL: localhost:5432

# View logs
docker-compose logs -f api
```

### 2. Database Setup
```bash
# Run migrations
npm run db:migrate

# Seed sample data (optional)
npm run db:seed
```

### 3. First API Call
```bash
# Register user
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }'

# Login and get token
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

---

## 📊 Database Schema Overview

### Core Tables (9 tables)

| Table | Purpose | Records |
|-------|---------|---------|
| `users` | User accounts & credentials | Người dùng |
| `cases` | Legal cases | Vụ án |
| `documents` | Uploaded documents | Tài liệu đã upload |
| `documents_versions` | Document change history | Lịch sử tài liệu |
| `case_summaries` | AI-generated summaries | Tóm tắt tự động |
| `chat_messages` | Chat history | Cuộc hội thoại |
| `brief_exports` | Generated briefs | Tờ trình được tạo |
| `audit_logs` | Action logging | Nhật ký kiểm tra |
| `processing_jobs` | Background job tracking | Công việc xử lý |

---

## 🔌 API Endpoints Summary

### Authentication (5 endpoints)
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập
- `POST /auth/refresh` - Làm mới token
- `POST /auth/logout` - Đăng xuất
- `GET /auth/profile` - Lấy thông tin người dùng

### Cases (8 endpoints)
- `GET /cases` - Danh sách vụ án
- `POST /cases` - Tạo vụ án
- `GET /cases/{id}` - Chi tiết vụ án
- `PUT /cases/{id}` - Chỉnh sửa vụ án
- `PATCH /cases/{id}/status` - Cập nhật trạng thái
- `DELETE /cases/{id}` - Xóa vụ án
- Multiple action endpoints

### Documents (10 endpoints)
- `POST /cases/{caseId}/documents/upload` - Upload tài liệu
- `GET /cases/{caseId}/documents` - Danh sách tài liệu
- `GET /documents/{id}` - Chi tiết tài liệu
- `PUT /documents/{id}` - Sửa thông tin
- `DELETE /documents/{id}` - Xóa tài liệu
- `GET /documents/{id}/download` - Tải xuống
- `POST /documents/{id}/reprocess` - Xử lý lại

### Chat (5 endpoints)
- `POST /cases/{caseId}/messages` - Gửi tin nhắn
- `GET /cases/{caseId}/messages` - Lịch sử chat
- `DELETE /messages/{id}` - Xóa tin nhắn
- `POST /messages/{id}/feedback` - Phản hồi

### Summaries & Briefs (8 endpoints)
- `GET /cases/{caseId}/summary` - Lấy tóm tắt
- `POST /cases/{caseId}/summary/generate` - Tạo tóm tắt
- `GET /cases/{caseId}/summary/status` - Kiểm tra trạng thái
- `PUT /cases/{caseId}/summary` - Chỉnh sửa tóm tắt
- `POST /cases/{caseId}/brief/generate` - Tạo tờ trình
- `GET /briefs/{id}/download` - Tải xuống tờ trình

### Search (2 endpoints)
- `GET /search/documents` - Tìm kiếm full-text
- `GET /search/semantic` - Tìm kiếm ngữ nghĩa

---

## 🔐 Security Features

- **Authentication**: JWT-based with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Validation**: Input validation on all endpoints
- **Rate limiting**: 1000 req/hour for standard users
- **Audit logging**: All user actions logged
- **Data protection**: PII masking in logs, soft deletes

---

## ⚡ Performance Optimization

### Caching
- Redis for sessions (24 hours)
- Case summaries (7 days)
- Document metadata (24 hours)
- Search results (1 hour)

### Database
- Connection pooling (10-50 connections)
- Proper indexing on all foreign keys
- Pagination with limit default 10-50
- Soft deletes for data integrity

### API
- Response compression (gzip)
- CDN for file serving
- Async processing with message queue
- Request batching support

---

## 📈 Scalability

### Horizontal Scaling
- Stateless API services (multiple instances)
- Load balancer for distribution
- Database read replicas
- Separate worker instances

### Vertical Scaling
- Caching layer reduces DB load
- Async processing queue
- Efficient indexing strategy
- Connection pooling

---

## 🧪 Testing

### Coverage Targets
- Unit tests: 40% (services, utilities)
- Integration tests: 30% (API endpoints, database)
- E2E tests: 20% (full user workflows)

### Test Tools
- Jest for Node.js unit tests
- Supertest for API integration tests
- Pytest for Python service tests
- k6 for load testing

---

## 📝 Documentation Files

| File | Mục đích | Kích thước |
|------|---------|-----------|
| BACKEND_DESIGN.md | Thiết kế hệ thống | 50+ pages |
| AI_PIPELINE.md | Quy trình AI/ML | 30+ pages |
| API_SPECIFICATIONS.md | Chi tiết API | 25+ pages |
| DEPLOYMENT_GUIDE.md | Hướng dẫn deploy | 35+ pages |
| IMPLEMENTATION_ROADMAP.md | Kế hoạch phát triển | 20+ pages |

**Tổng cộng**: 160+ trang tài liệu chi tiết

---

## 🎯 Next Steps

### 1. Review Documentation
- [ ] Read BACKEND_DESIGN.md for overall architecture
- [ ] Check API_SPECIFICATIONS.md for endpoint details
- [ ] Review DEPLOYMENT_GUIDE.md for infrastructure setup

### 2. Setup Development Environment
- [ ] Install Docker & Docker Compose
- [ ] Clone repository
- [ ] Run `docker-compose up`
- [ ] Verify all services are running

### 3. Start Development
- [ ] Follow IMPLEMENTATION_ROADMAP.md Phase 1
- [ ] Setup authentication API (Week 1)
- [ ] Implement case management (Week 2)
- [ ] Add document upload (Week 3)

### 4. Implementation Order
1. **Foundation**: Auth, Database, Basic CRUD
2. **File Handling**: Upload, Storage, Metadata
3. **Processing**: OCR, NLP, Summarization
4. **Intelligence**: Chat, RAG, Embeddings
5. **Polish**: Testing, Optimization, Deployment

---

## 💡 Key Design Decisions

1. **Message Queue**: RabbitMQ for async document processing
2. **AI Services**: Separate Python service for ML workloads
3. **Caching**: Redis for frequently accessed data
4. **Search**: Elasticsearch for full-text document search
5. **Storage**: S3-compatible for file storage
6. **Database**: PostgreSQL for transactional data integrity
7. **API Style**: RESTful v1 with JSON responses
8. **Authentication**: JWT with refresh tokens

---

## 📞 Support & References

### Documentation Links
- Node.js: https://nodejs.org/docs/
- Express.js: https://expressjs.com/
- PostgreSQL: https://www.postgresql.org/docs/
- Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
- Python Transformers: https://huggingface.co/docs/transformers/

### Tools
- Postman: For API testing
- DBeaver: For database management
- Docker Desktop: For containerization
- Kubernetes: For production orchestration

---

## ✅ Checklist Before Development

- [ ] All documentation reviewed by team
- [ ] Development environment setup tested
- [ ] Database schema validated
- [ ] API contracts agreed upon
- [ ] AI/ML models selected and tested
- [ ] Infrastructure planned and budgeted
- [ ] Security requirements understood
- [ ] Performance requirements defined
- [ ] Team trained on architecture
- [ ] Git workflow established

---

**Created**: February 7, 2026  
**Version**: 1.0  
**Status**: Ready for Development  

---

## License & Usage

These design documents are proprietary and confidential. Use only within your organization.

