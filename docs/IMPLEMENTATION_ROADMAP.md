# Implementation Roadmap & Development Guide

## 1. DEVELOPMENT PHASES

### Phase 1: MVP - Core Infrastructure (Weeks 1-4)

#### Week 1: Setup & Authentication
- [ ] Initialize Node.js/Express backend with TypeScript
- [ ] Setup PostgreSQL database and schema
- [ ] Implement JWT authentication system
- [ ] Create user registration and login endpoints
- [ ] Setup Docker environment

**Deliverables:**
- Login/Register API working
- Docker development environment
- Basic user CRUD operations

#### Week 2: Case Management
- [ ] Create Cases CRUD endpoints
- [ ] Implement case status workflow
- [ ] Setup case-user relationship
- [ ] Create case list with filtering
- [ ] Add basic case details retrieval

**Deliverables:**
- Cases management API (GET, POST, PUT, DELETE)
- Cases list with pagination and search
- Status update endpoints

#### Week 3: Document Upload & Storage
- [ ] Integrate AWS S3 or Azure Blob Storage
- [ ] Implement file upload API with multipart handling
- [ ] Add document labeling system
- [ ] Setup file storage paths and access control
- [ ] Implement document CRUD operations

**Deliverables:**
- Document upload API
- File storage integration
- Document metadata database operations

#### Week 4: Message Queue & Basic Processing
- [ ] Setup RabbitMQ infrastructure
- [ ] Create message queue handlers
- [ ] Implement background job structure
- [ ] Setup worker service skeleton
- [ ] Create basic document status tracking

**Deliverables:**
- RabbitMQ integration with Node.js
- Basic message queue working
- Worker service running

---

### Phase 2: AI Integration (Weeks 5-8)

#### Week 5: OCR Service
- [ ] Setup Python Flask AI service
- [ ] Implement Tesseract OCR wrapper
- [ ] Add PDF text extraction (pdfplumber)
- [ ] Add document preprocessing (OpenCV)
- [ ] Implement language detection

**Deliverables:**
- OCR service returning text from documents
- Confidence scoring system
- Multi-page document handling

#### Week 6: NLP & Entity Extraction
- [ ] Integrate VnCoreNLP for Vietnamese processing
- [ ] Implement entity extraction (people, organizations, dates, money)
- [ ] Add keyword extraction using TF-IDF
- [ ] Create entity storage in database
- [ ] Implement spaCy for English support

**Deliverables:**
- Entity extraction from documents
- Key terms identification
- Multi-language support

#### Week 7: Summarization & Embeddings
- [ ] Implement extractive summarization
- [ ] Add abstractive summarization (transformer models)
- [ ] Generate embeddings using Sentence Transformers
- [ ] Setup vector database or storage
- [ ] Create semantic search capability

**Deliverables:**
- Document summarization API
- Embedding generation working
- Summary storage and retrieval

#### Week 8: AI Pipeline Integration
- [ ] Create complete document processing pipeline
- [ ] Connect all AI services to message queue
- [ ] Implement progress tracking
- [ ] Error handling and retry logic
- [ ] Performance optimization

**Deliverables:**
- End-to-end document processing
- Status updates in database
- Error logging and recovery

---

### Phase 3: Chat & Retrieval (Weeks 9-10)

#### Week 9: Chat Interface Backend
- [ ] Implement chat message storage
- [ ] Create message retrieval API
- [ ] Setup document context retrieval
- [ ] Implement citation tracking
- [ ] Create search-in-documents functionality

**Deliverables:**
- Chat messages persisted
- Message retrieval with pagination
- Document search integrated

#### Week 10: AI-Powered Chat
- [ ] Integrate LLM (OpenAI GPT-4 or local alternative)
- [ ] Implement RAG (Retrieval Augmented Generation)
- [ ] Create prompt engineering templates
- [ ] Add citation generation
- [ ] Setup response streaming

**Deliverables:**
- AI chatbot responding to questions
- Citations from documents
- Context-aware responses

---

### Phase 4: Advanced Features (Weeks 11-12)

#### Week 11: Brief Generation
- [ ] Create brief/petition templates
- [ ] Implement template variable substitution
- [ ] Add DOCX generation capability
- [ ] Implement PDF export
- [ ] Create customization options

**Deliverables:**
- Brief generation from case data
- Multiple export formats
- Template customization

#### Week 12: Polish & Optimization
- [ ] Performance optimization
- [ ] Caching strategy implementation
- [ ] Rate limiting setup
- [ ] Error handling improvements
- [ ] Production deployment preparation

**Deliverables:**
- Production-ready backend
- Performance benchmarks
- Deployment ready

---

## 2. TECHNOLOGY IMPLEMENTATION DETAILS

### 2.1 Node.js API Backend - Express Setup

```typescript
// backend/api/src/index.ts

import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { Pool } from 'pg';
import Redis from 'ioredis';
import amqp from 'amqplib';
import { Logger } from 'winston';

import authRoutes from './routes/auth.routes';
import casesRoutes from './routes/cases.routes';
import documentsRoutes from './routes/documents.routes';
import messagesRoutes from './routes/messages.routes';
import healthRoutes from './routes/health.routes';

import { errorHandler } from './middleware/error-handler';
import { authenticateToken } from './middleware/auth';
import { createLogger } from './utils/logger';

const app: Express = express();
const PORT = process.env.PORT || 3000;
const logger: Logger = createLogger();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ALLOWED_ORIGINS?.split(','),
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Logging
app.use(morgan('combined', { stream: { write: msg => logger.info(msg) } }));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Database connection
const db = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

db.on('error', (err) => {
  logger.error('Database connection error:', err);
});

// Redis connection
const redis = new Redis({
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  retryStrategy: (times) => Math.min(times * 50, 2000)
});

redis.on('error', (err) => {
  logger.error('Redis connection error:', err);
});

// RabbitMQ connection
let rabbitmqChannel: amqp.Channel;

async function connectRabbitMQ() {
  try {
    const connection = await amqp.connect(
      process.env.RABBITMQ_URL || 'amqp://localhost:5672'
    );
    rabbitmqChannel = await connection.createChannel();
    
    // Declare queues
    await rabbitmqChannel.assertQueue('document.upload', { durable: true });
    await rabbitmqChannel.assertQueue('document.process', { durable: true });
    await rabbitmqChannel.assertQueue('case.summary', { durable: true });
    await rabbitmqChannel.assertQueue('brief.export', { durable: true });
    
    logger.info('Connected to RabbitMQ');
  } catch (err) {
    logger.error('RabbitMQ connection error:', err);
    setTimeout(connectRabbitMQ, 5000); // Retry
  }
}

// Routes
app.use('/api/health', healthRoutes);
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/cases', authenticateToken, casesRoutes);
app.use('/api/v1/documents', authenticateToken, documentsRoutes);
app.use('/api/v1/messages', authenticateToken, messagesRoutes);

// Error handling
app.use(errorHandler);

// Start server
async function start() {
  try {
    // Test database connection
    await db.query('SELECT NOW()');
    logger.info('Database connected');
    
    // Connect to RabbitMQ
    await connectRabbitMQ();
    
    // Start server
    app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
    });
  } catch (err) {
    logger.error('Failed to start server:', err);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, closing connections...');
  await db.end();
  redis.disconnect();
  process.exit(0);
});

start();

export { app, db, redis, rabbitmqChannel };
```

### 2.2 Python AI Service - Flask Setup

```python
# backend/ai-service/app/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from dotenv import load_dotenv
import pika
import json

from services.ocr_service import OCRService
from services.nlp_service import NLPService
from services.summarization_service import SummarizationService
from services.embedding_service import EmbeddingService

load_dotenv()

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize services
ocr_service = OCRService()
nlp_service = NLPService()
summarization_service = SummarizationService()
embedding_service = EmbeddingService()

# RabbitMQ connection
def get_rabbitmq_connection():
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(
        host='rabbitmq',
        port=5672,
        credentials=credentials,
        connection_attempts=3,
        retry_delay=2
    )
    return pika.BlockingConnection(parameters)

# Routes
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/ocr/process', methods=['POST'])
@limiter.limit("10 per minute")
async def process_ocr():
    try:
        file_url = request.json.get('file_url')
        file_type = request.json.get('file_type')
        
        if not file_url or not file_type:
            return jsonify({'error': 'Missing parameters'}), 400
        
        # Download and process file
        result = await ocr_service.process_document(file_url, file_type)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'OCR error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/nlp/extract-entities', methods=['POST'])
@limiter.limit("20 per minute")
async def extract_entities():
    try:
        text = request.json.get('text')
        language = request.json.get('language', 'vi')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        entities = await nlp_service.extract_entities(text, language)
        
        return jsonify(entities), 200
    
    except Exception as e:
        logger.error(f'NLP error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarization/summarize', methods=['POST'])
@limiter.limit("5 per minute")
async def summarize():
    try:
        text = request.json.get('text')
        language = request.json.get('language', 'vi')
        summary_ratio = request.json.get('summary_ratio', 0.3)
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        result = await summarization_service.summarize(
            text,
            language,
            summary_ratio
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'Summarization error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/embeddings/generate', methods=['POST'])
@limiter.limit("50 per minute")
async def generate_embedding():
    try:
        text = request.json.get('text')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        embedding = await embedding_service.generate_embedding(text)
        
        return jsonify({
            'embedding': embedding,
            'dimension': len(embedding)
        }), 200
    
    except Exception as e:
        logger.error(f'Embedding error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f'Internal error: {str(e)}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

## 3. IMPLEMENTATION PRIORITY MATRIX

### High Priority, High Effort
1. Complete document processing pipeline
2. Kubernetes production deployment
3. AI-powered chat with RAG

### High Priority, Low Effort
1. Document upload API
2. Basic case CRUD
3. Authentication system
4. Database schema

### Medium Priority, Low Effort
1. Pagination and filtering
2. Document labeling
3. Basic error handling
4. Logging system

### Medium Priority, High Effort
1. Full-text search with Elasticsearch
2. Advanced caching strategies
3. Load testing and optimization

---

## 4. TESTING STRATEGY

### Unit Tests (40% coverage target)
```typescript
// Example test structure
describe('CasesService', () => {
  let casesService: CasesService;
  let mockDb: jest.Mocked<Pool>;
  
  beforeEach(() => {
    mockDb = createMockPool();
    casesService = new CasesService(mockDb);
  });
  
  describe('createCase', () => {
    it('should create a new case with valid data', async () => {
      const caseData = { title: 'Test Case', ... };
      const result = await casesService.createCase(caseData);
      expect(result).toHaveProperty('id');
    });
  });
});
```

### Integration Tests (30% coverage target)
```typescript
// API endpoint testing
describe('POST /api/v1/cases', () => {
  it('should create case and return 201', async () => {
    const response = await request(app)
      .post('/api/v1/cases')
      .set('Authorization', `Bearer ${token}`)
      .send(caseData);
    
    expect(response.status).toBe(201);
    expect(response.body.data).toHaveProperty('id');
  });
});
```

### E2E Tests (20% coverage target)
- Full user workflows
- Multi-step processes
- Real database/API calls

---

## 5. KEY PERFORMANCE INDICATORS (KPIs)

### API Performance
- Average response time: < 200ms
- P95 response time: < 500ms
- Availability: > 99.5%

### Document Processing
- OCR success rate: > 95%
- Average processing time: < 30 seconds per document
- Entity extraction accuracy: > 90%

### User Experience
- Page load time: < 1 second
- Chat response time: < 2 seconds
- Upload success rate: > 99%

---

## 6. RESOURCE REQUIREMENTS

### Development Team
- 1 Backend Lead (Node.js)
- 1 Python/ML Engineer
- 1 DevOps Engineer
- 1 Frontend Developer (already exists)
- 1 QA Engineer

### Infrastructure (Production)
- Kubernetes cluster (min 3 nodes, 2 CPU, 4GB RAM each)
- PostgreSQL managed service (db.t3.xlarge)
- Redis cluster (3 nodes)
- RabbitMQ cluster (3 nodes)
- S3-compatible storage (500GB initial)

### Development Infrastructure
- Local machine (8GB RAM, 4 CPU)
- Docker enabled
- Git repository

---

## 7. RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| OCR accuracy issues | Medium | High | Implement fallback, manual correction |
| Performance bottleneck | Medium | High | Load testing, caching, monitoring |
| Data security breach | Low | Critical | Encryption, audit logs, regular security audits |
| Service outage | Low | High | Redundancy, failover, backups |
| Team knowledge gaps | Medium | Medium | Documentation, training |
| Scope creep | High | Medium | Strict requirement management |

---

## 8. SUCCESS CRITERIA

- [ ] MVP deployed to production
- [ ] 100+ test cases passing
- [ ] > 80% code coverage
- [ ] Average API response < 200ms
- [ ] OCR accuracy > 95%
- [ ] Zero critical security vulnerabilities
- [ ] Documentation complete
- [ ] Team trained and ready for handoff

