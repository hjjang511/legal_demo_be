# Deployment & Infrastructure Guide

## 1. LOCAL DEVELOPMENT SETUP

### 1.1 Prerequisites

```bash
# System requirements
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+
- Git

# Install Node dependencies
cd legal_demo
npm install

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Docker Compose Setup (Local Development)

**docker-compose.yml**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: legal-demo-postgres
    environment:
      POSTGRES_DB: legal_demo
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init-schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: legal-demo-redis
    ports:
      - "6379:6379"
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # RabbitMQ Message Queue
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    container_name: legal-demo-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Elasticsearch for full-text search
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    container_name: legal-demo-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # VnCoreNLP Service
  vncorenlp:
    image: vncorenlp/vncorenlp:latest
    container_name: legal-demo-vncorenlp
    ports:
      - "9000:9000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Node.js API Server
  api:
    build:
      context: ./backend/api
      dockerfile: Dockerfile
    container_name: legal-demo-api
    environment:
      NODE_ENV: development
      PORT: 3000
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: legal_demo
      DB_USER: postgres
      DB_PASSWORD: postgres
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: redis_password
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672
      JWT_SECRET: dev-secret-key-min-32-chars-here
      S3_BUCKET: legal-demo-dev
      AWS_REGION: us-east-1
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    volumes:
      - ./backend/api:/app
      - /app/node_modules
    command: npm run dev

  # Python AI Processing Service
  ai-service:
    build:
      context: ./backend/ai-service
      dockerfile: Dockerfile
    container_name: legal-demo-ai-service
    environment:
      FLASK_ENV: development
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672
      VNCORENLP_URL: http://vncorenlp:9000
      LOG_LEVEL: info
    ports:
      - "5000:5000"
    depends_on:
      rabbitmq:
        condition: service_healthy
      vncorenlp:
        condition: service_healthy
    volumes:
      - ./backend/ai-service:/app
      - ai_cache:/app/.cache
    command: python -m flask run --host=0.0.0.0

  # Background Job Worker
  worker:
    build:
      context: ./backend/worker
      dockerfile: Dockerfile
    container_name: legal-demo-worker
    environment:
      NODE_ENV: development
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: legal_demo
      DB_USER: postgres
      DB_PASSWORD: postgres
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672
      AI_SERVICE_URL: http://ai-service:5000
    depends_on:
      rabbitmq:
        condition: service_healthy
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/worker:/app
      - /app/node_modules
    command: npm start

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  elasticsearch_data:
  ai_cache:

networks:
  default:
    name: legal-demo-network
```

**Start all services:**
```bash
docker-compose up -d

# View logs
docker-compose logs -f api

# Access services:
# - API: http://localhost:3000
# - RabbitMQ UI: http://localhost:15672
# - Elasticsearch: http://localhost:9200
# - Redis: localhost:6379
```

---

## 2. BACKEND PROJECT STRUCTURE

### 2.1 API Service Structure

```
backend/
├── api/
│   ├── src/
│   │   ├── config/
│   │   │   ├── database.ts
│   │   │   ├── redis.ts
│   │   │   └── rabbitmq.ts
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth.ts
│   │   │   ├── error-handler.ts
│   │   │   ├── rate-limiter.ts
│   │   │   └── logger.ts
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.routes.ts
│   │   │   ├── cases.routes.ts
│   │   │   ├── documents.routes.ts
│   │   │   ├── messages.routes.ts
│   │   │   └── health.routes.ts
│   │   │
│   │   ├── controllers/
│   │   │   ├── auth.controller.ts
│   │   │   ├── cases.controller.ts
│   │   │   ├── documents.controller.ts
│   │   │   ├── messages.controller.ts
│   │   │   └── search.controller.ts
│   │   │
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── cases.service.ts
│   │   │   ├── documents.service.ts
│   │   │   ├── messages.service.ts
│   │   │   ├── case-summary.service.ts
│   │   │   ├── brief.service.ts
│   │   │   └── search.service.ts
│   │   │
│   │   ├── models/
│   │   │   ├── user.ts
│   │   │   ├── case.ts
│   │   │   ├── document.ts
│   │   │   └── message.ts
│   │   │
│   │   ├── repositories/
│   │   │   ├── user.repository.ts
│   │   │   ├── case.repository.ts
│   │   │   ├── document.repository.ts
│   │   │   └── message.repository.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── validators.ts
│   │   │   ├── formatters.ts
│   │   │   └── file-upload.ts
│   │   │
│   │   └── index.ts  # Main app entry
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
│
├── worker/
│   ├── src/
│   │   ├── processors/
│   │   │   ├── ocr.processor.ts
│   │   │   ├── nlp.processor.ts
│   │   │   ├── summarization.processor.ts
│   │   │   └── embedding.processor.ts
│   │   │
│   │   ├── consumers/
│   │   │   ├── document-upload.consumer.ts
│   │   │   ├── brief-generation.consumer.ts
│   │   │   └── summary-generation.consumer.ts
│   │   │
│   │   ├── queues/
│   │   │   └── queue.ts
│   │   │
│   │   └── index.ts
│   │
│   ├── Dockerfile
│   ├── package.json
│   └── .env.example
│
└── ai-service/
    ├── app/
    │   ├── services/
    │   │   ├── ocr_service.py
    │   │   ├── nlp_service.py
    │   │   ├── summarization_service.py
    │   │   └── embedding_service.py
    │   │
    │   ├── routes/
    │   │   ├── ocr_routes.py
    │   │   └── nlp_routes.py
    │   │
    │   ├── utils/
    │   │   ├── preprocessing.py
    │   │   └── models.py
    │   │
    │   └── app.py  # Flask app
    │
    ├── Dockerfile
    ├── requirements.txt
    ├── Makefile
    └── .env.example
```

---

## 3. DOCKERFILE EXAMPLES

### 3.1 API Service Dockerfile

**backend/api/Dockerfile**
```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install dumb-init to handle signals properly
RUN apk add --no-cache dumb-init

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --production

# Copy built app from builder
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Use dumb-init as entrypoint
ENTRYPOINT ["dumb-init", "node", "dist/index.js"]
```

### 3.2 Python AI Service Dockerfile

**backend/ai-service/Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY app ./app

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app.app:app"]
```

---

## 4. KUBERNETES DEPLOYMENT

### 4.1 Kubernetes Manifests

**k8s/api-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-demo-api
  namespace: legal-demo
  labels:
    app: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/legal-demo-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 3000
          name: http
        
        env:
        - name: NODE_ENV
          value: "production"
        - name: DB_HOST
          value: postgres-service
        - name: DB_PORT
          value: "5432"
        - name: REDIS_HOST
          value: redis-service
        - name: RABBITMQ_URL
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret
        
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: legal-demo
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
```

**k8s/postgres-statefulset.yaml**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: legal-demo
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        
        env:
        - name: POSTGRES_DB
          value: legal_demo
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: legal-demo
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### 4.2 Apply Kubernetes Configuration

```bash
# Create namespace
kubectl create namespace legal-demo

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=password=your-secure-password \
  -n legal-demo

kubectl create secret generic jwt-secret \
  --from-literal=secret=your-jwt-secret-min-32-chars \
  -n legal-demo

# Apply manifests
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/ai-service-deployment.yaml

# Check status
kubectl get pods -n legal-demo
kubectl get services -n legal-demo

# View logs
kubectl logs -f deployment/legal-demo-api -n legal-demo
```

---

## 5. CI/CD PIPELINE

### 5.1 GitHub Actions Workflow

**.github/workflows/deploy.yml**
```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: 'backend/api/package-lock.json'
    
    - name: Install dependencies
      working-directory: ./backend/api
      run: npm ci
    
    - name: Run linter
      working-directory: ./backend/api
      run: npm run lint
    
    - name: Run tests
      working-directory: ./backend/api
      run: npm test -- --coverage
      env:
        DB_HOST: localhost
        DB_USER: postgres
        DB_PASSWORD: postgres
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./backend/api/coverage/lcov.info

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push API image
      uses: docker/build-push-action@v4
      with:
        context: ./backend/api
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }}
        cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:buildcache
        cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:buildcache,mode=max
    
    - name: Build and push AI Service image
      uses: docker/build-push-action@v4
      with:
        context: ./backend/ai-service
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-service:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-service:${{ github.sha }}
        cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-service:buildcache
        cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-service:buildcache,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      env:
        KUBECONFIG: ${{ secrets.KUBECONFIG }}
      run: |
        kubectl set image deployment/legal-demo-api \
          api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }} \
          -n legal-demo
        
        kubectl set image deployment/legal-demo-ai-service \
          ai-service=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-service:${{ github.sha }} \
          -n legal-demo
        
        kubectl rollout status deployment/legal-demo-api -n legal-demo
```

---

## 6. ENVIRONMENT VARIABLES

**backend/api/.env.production**
```bash
# Server
NODE_ENV=production
PORT=3000
LOG_LEVEL=info

# Database
DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=legal_demo
DB_USER=postgres
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_SSL=true
DB_POOL_MIN=5
DB_POOL_MAX=20

# Redis
REDIS_HOST=redis-service
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=0

# JWT
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRES_IN=3600
REFRESH_TOKEN_SECRET=${REFRESH_TOKEN_SECRET}
REFRESH_TOKEN_EXPIRES_IN=604800

# RabbitMQ
RABBITMQ_URL=amqp://guest:${RABBITMQ_PASSWORD}@rabbitmq-service:5672

# AWS S3
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REGION=us-east-1
S3_BUCKET=legal-demo-prod
S3_BASE_URL=https://s3.amazonaws.com/legal-demo-prod

# AI Services
AI_SERVICE_URL=http://ai-service:5000
OCR_TIMEOUT=300000
SUMMARIZATION_TIMEOUT=120000

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com
SESSION_SECRET=${SESSION_SECRET}

# Rate Limiting
RATE_LIMIT_WINDOW_MS=3600000
RATE_LIMIT_MAX_REQUESTS=1000

# Monitoring
DATADOG_API_KEY=${DATADOG_API_KEY}
SENTRY_DSN=${SENTRY_DSN}
```

---

## 7. DATABASE MIGRATIONS

### 7.1 Database Schema Creation

**db/init-schema.sql**
```sql
-- Run migrations on container startup
-- Or use Liquibase/Flyway for version control

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- All table definitions go here
-- (See BACKEND_DESIGN.md for complete schema)
```

### 7.2 Running Migrations

```bash
# One-time initial setup
npm run db:migrate:initial

# Migrate for updates
npm run db:migrate

# Rollback if needed
npm run db:rollback
```

---

## 8. MONITORING & LOGGING

### 8.1 Prometheus Metrics

**Install monitoring stack:**
```bash
# Already included in docker-compose with Prometheus port
# Add to docker-compose.yml:

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
```

### 8.2 ELK Stack for Logging

```bash
# Elasticsearch, Logstash, Kibana
# Use docker-compose.yml service defined above
```

---

## 9. PRODUCTION CHECKLIST

- [ ] Enable SSL/TLS for all connections
- [ ] Set up database backups (daily)
- [ ] Configure auto-scaling policies
- [ ] Set up monitoring and alerting
- [ ] Enable request logging and auditing
- [ ] Configure firewall rules
- [ ] Set up CDN for static assets
- [ ] Enable rate limiting
- [ ] Regular security updates (weekly)
- [ ] Database optimization (indexing)
- [ ] Set up disaster recovery plan
- [ ] Load testing before go-live

