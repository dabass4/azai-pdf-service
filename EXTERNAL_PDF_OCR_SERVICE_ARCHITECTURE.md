# External PDF/OCR Processing Service - Architecture Design

## Executive Summary

This document outlines a scalable, production-ready architecture for offloading PDF and OCR processing from the main application to external services. This approach addresses current performance issues, eliminates dependency persistence problems, and provides a foundation for high-volume document processing.

---

## Table of Contents

1. [Current Architecture](#current-architecture)
2. [Proposed Architecture](#proposed-architecture)
3. [Benefits & Trade-offs](#benefits--trade-offs)
4. [Service Specifications](#service-specifications)
5. [API Endpoints](#api-endpoints)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Security Considerations](#security-considerations)
8. [Cost Analysis](#cost-analysis)
9. [Migration Strategy](#migration-strategy)
10. [Monitoring & Observability](#monitoring--observability)

---

## Current Architecture

### Overview
```
┌─────────────────────────────────────────────────────────┐
│                   Main Application                       │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  FastAPI   │  │   React    │  │    MongoDB       │  │
│  │  Backend   │  │  Frontend  │  │                  │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
│         │                                                │
│         ├─── pdf2image (poppler-utils) ⚠️               │
│         ├─── Gemini Vision API (external) ✅            │
│         └─── Synchronous processing ⚠️                   │
└─────────────────────────────────────────────────────────┘
```

### Current Flow
1. User uploads PDF to main application
2. Backend saves file temporarily
3. **In-process**: Convert PDF pages to images (poppler-utils)
4. **External API**: Send images to Gemini Vision for OCR
5. Backend processes extracted data
6. Store results in MongoDB
7. Return response to user

### Current Issues

#### Critical Problems:
- ⚠️ **Poppler dependency persistence**: Lost on container restarts (recurring 4+ times)
- ⚠️ **Resource consumption**: Heavy processing blocks application threads
- ⚠️ **Scalability**: Can't scale PDF processing independently
- ⚠️ **Timeout risk**: Large multi-page PDFs may exceed request timeouts
- ⚠️ **Memory usage**: Multiple concurrent uploads strain server memory

#### Medium Issues:
- Limited retry logic for failed conversions
- No processing queue for batch operations
- Single point of failure
- Difficult to optimize/monitor PDF processing separately

---

## Proposed Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Application                            │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐          │
│  │  FastAPI   │  │   React    │  │    MongoDB       │          │
│  │  Backend   │  │  Frontend  │  │                  │          │
│  └─────┬──────┘  └────────────┘  └──────────────────┘          │
│        │                                                         │
│        │ HTTP/REST API                                          │
└────────┼─────────────────────────────────────────────────────────┘
         │
         │
┌────────▼─────────────────────────────────────────────────────────┐
│              API Gateway / Load Balancer                          │
│                   (nginx / AWS ALB)                               │
└────────┬──────────────────────────────┬──────────────────────────┘
         │                              │
         │                              │
┌────────▼──────────────┐     ┌─────────▼─────────────────────────┐
│  PDF Processing       │     │   Background Job Queue             │
│  Service              │     │   (Redis + Celery / AWS SQS)      │
│  ┌─────────────────┐ │     │                                    │
│  │ FastAPI Server  │ │     │   ┌──────────────────────────┐    │
│  │ + poppler-utils │ │     │   │  Worker Pool (async)     │    │
│  │ + pdf2image     │ │     │   │  - PDF conversion jobs   │    │
│  └─────────────────┘ │     │   │  - OCR processing jobs   │    │
│                      │     │   │  - Batch operations      │    │
│  Docker Container    │     │   └──────────────────────────┘    │
└──────────────────────┘     └───────────────────────────────────┘
         │
         │
┌────────▼──────────────────────────────────────────────────────────┐
│              External OCR Services                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Gemini Vision  │  │  Tesseract OCR   │  │  AWS Textract   │ │
│  │  API (current)  │  │  (self-hosted)   │  │  (optional)     │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. PDF Processing Service (New)
**Technology**: FastAPI + Docker
**Responsibilities**:
- PDF to image conversion (poppler-utils)
- PDF metadata extraction
- Page splitting for multi-page documents
- Image optimization and compression
- Health checks and status monitoring

**Why FastAPI?**
- Async/await support for concurrent processing
- Automatic OpenAPI documentation
- Easy integration with existing stack
- High performance (comparable to Node.js/Go)

#### 2. Background Job Queue (New)
**Technology Options**:
- **Option A**: Redis + Celery (Python-native)
- **Option B**: AWS SQS + Lambda (serverless)
- **Option C**: RabbitMQ + Worker pool (enterprise)

**Responsibilities**:
- Async job management
- Retry logic with exponential backoff
- Job prioritization
- Dead letter queue for failed jobs
- Progress tracking

#### 3. API Gateway (Enhancement)
**Technology**: Nginx or AWS ALB
**Responsibilities**:
- Request routing
- Load balancing across workers
- Rate limiting
- API key validation
- SSL/TLS termination

#### 4. Main Application (Modified)
**Changes**:
- Replace in-process PDF conversion with API calls
- Implement async upload handling
- Add webhook support for job completion
- Enhance error handling and retry logic

---

## Benefits & Trade-offs

### Benefits

#### Performance
✅ **Independent Scaling**: Scale PDF processing separately from main app
✅ **No Blocking**: Async processing doesn't block user requests
✅ **Resource Optimization**: Dedicated resources for heavy processing
✅ **Better Timeouts**: No risk of request timeouts on large files

#### Reliability
✅ **Dependency Isolation**: Poppler-utils issues don't affect main app
✅ **Fault Tolerance**: Service failures don't crash entire application
✅ **Retry Logic**: Built-in job retry for transient failures
✅ **Graceful Degradation**: Can fall back to alternative OCR services

#### Maintainability
✅ **Separation of Concerns**: Clear boundaries between services
✅ **Independent Deployment**: Update PDF service without touching main app
✅ **Easier Debugging**: Isolated logs and monitoring
✅ **Technology Flexibility**: Can swap PDF libraries without affecting core app

#### Cost Efficiency
✅ **Autoscaling**: Scale down during low usage
✅ **Spot Instances**: Use cheaper compute for background jobs
✅ **Resource Optimization**: Right-size each service independently

### Trade-offs

#### Complexity
⚠️ **More Moving Parts**: Additional services to manage and monitor
⚠️ **Network Latency**: API calls add network overhead
⚠️ **Distributed Systems**: Need to handle network failures, retries
⚠️ **Testing Complexity**: Integration tests more complex

#### Infrastructure
⚠️ **Additional Costs**: More servers/containers to run
⚠️ **DevOps Overhead**: More deployment pipelines
⚠️ **Monitoring**: Need to monitor multiple services

#### Development
⚠️ **Migration Effort**: Requires refactoring existing code
⚠️ **Learning Curve**: Team needs to understand distributed architecture
⚠️ **API Versioning**: Need to manage API contracts between services

---

## Service Specifications

### PDF Processing Service

#### Technology Stack
```yaml
Language: Python 3.11+
Framework: FastAPI 0.100+
Dependencies:
  - pdf2image: PDF to image conversion
  - poppler-utils: System dependency (pre-installed in Docker)
  - Pillow: Image processing and optimization
  - aiofiles: Async file operations
  - httpx: Async HTTP client for OCR APIs
  
Infrastructure:
  - Docker container
  - 2 CPU cores, 4GB RAM (baseline)
  - Autoscaling: 1-10 instances
  - Storage: Ephemeral (temp files cleaned automatically)
```

#### Endpoints

**1. Health Check**
```http
GET /health
Response: 200 OK
{
  "status": "healthy",
  "poppler_version": "22.12.0",
  "service": "pdf-processing",
  "uptime_seconds": 3600
}
```

**2. Convert PDF to Images**
```http
POST /api/v1/pdf/convert
Headers:
  Authorization: Bearer {API_KEY}
  Content-Type: multipart/form-data

Body:
  file: <PDF file>
  dpi: 200 (optional, default: 200)
  format: "jpeg" | "png" (optional, default: "jpeg")
  quality: 95 (optional, 1-100)
  first_page: 1 (optional)
  last_page: null (optional)

Response: 202 Accepted
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "pages": 5,
  "callback_url": null,
  "estimated_completion": "2024-12-15T17:00:00Z"
}
```

**3. Get Job Status**
```http
GET /api/v1/jobs/{job_id}
Headers:
  Authorization: Bearer {API_KEY}

Response: 200 OK
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "pages_processed": 5,
  "total_pages": 5,
  "results": [
    {
      "page": 1,
      "image_url": "https://s3.amazonaws.com/bucket/image1.jpg",
      "width": 1200,
      "height": 1600
    }
  ],
  "created_at": "2024-12-15T16:55:00Z",
  "completed_at": "2024-12-15T16:55:30Z"
}
```

**4. Extract PDF Metadata**
```http
POST /api/v1/pdf/metadata
Headers:
  Authorization: Bearer {API_KEY}
  Content-Type: multipart/form-data

Body:
  file: <PDF file>

Response: 200 OK
{
  "pages": 5,
  "author": "John Doe",
  "title": "Healthcare Timesheet",
  "created": "2024-12-01T10:00:00Z",
  "file_size_bytes": 1024000,
  "pdf_version": "1.4"
}
```

#### Docker Configuration

**Dockerfile**
```dockerfile
FROM python:3.11-slim

# Install poppler-utils and system dependencies
RUN apt-get update && \
    apt-get install -y \
    poppler-utils \
    libpoppler-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directory for file processing
RUN mkdir -p /tmp/pdf_processing && chmod 777 /tmp/pdf_processing

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  pdf-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${PDF_SERVICE_API_KEY}
      - MAX_FILE_SIZE_MB=50
      - TEMP_DIR=/tmp/pdf_processing
      - LOG_LEVEL=INFO
    volumes:
      - pdf_temp:/tmp/pdf_processing
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  pdf_temp:
  redis_data:
```

---

## API Endpoints

### Main Application Changes

#### Updated Upload Flow

**1. Upload PDF (Non-blocking)**
```http
POST /api/timesheets/upload
Headers:
  Authorization: Bearer {USER_TOKEN}
  Content-Type: multipart/form-data

Body:
  file: <PDF file>

Response: 202 Accepted
{
  "id": "ts_123456",
  "status": "processing",
  "message": "Timesheet is being processed",
  "estimated_completion_seconds": 30,
  "webhook_url": "/api/webhooks/timesheet/ts_123456"
}
```

**2. Check Processing Status**
```http
GET /api/timesheets/{timesheet_id}/status
Headers:
  Authorization: Bearer {USER_TOKEN}

Response: 200 OK
{
  "id": "ts_123456",
  "status": "processing",  // processing, completed, failed
  "progress": 60,
  "current_step": "extracting_data",
  "pages_processed": 3,
  "total_pages": 5,
  "error_message": null
}
```

**3. Webhook for Completion (Backend → Frontend)**
```http
POST /api/webhooks/timesheet/{timesheet_id}
Headers:
  X-Webhook-Signature: {HMAC_SIGNATURE}

Body:
{
  "timesheet_id": "ts_123456",
  "status": "completed",
  "extracted_data": {...},
  "processing_time_ms": 28500
}
```

---

## Implementation Roadmap

### Phase 1: Setup Infrastructure (Week 1-2)

#### Tasks:
1. **Create PDF Processing Service**
   - Set up FastAPI project structure
   - Implement health check endpoint
   - Build Docker image with poppler-utils
   - Test locally

2. **Set up Background Queue**
   - Choose technology (Redis + Celery recommended)
   - Configure job queue and workers
   - Implement basic job lifecycle

3. **Deploy to Staging**
   - Set up container orchestration (Docker Swarm/K8s/ECS)
   - Configure networking and load balancer
   - Set up monitoring and logging

**Deliverables:**
- ✅ PDF service running in Docker
- ✅ Background job queue operational
- ✅ Staging environment ready

### Phase 2: Build Core Features (Week 3-4)

#### Tasks:
1. **PDF Conversion Endpoints**
   - Implement /api/v1/pdf/convert
   - Add job status tracking
   - Implement retry logic

2. **Integration with Main App**
   - Update upload endpoint to use PDF service
   - Implement webhook handling
   - Add status polling

3. **Error Handling**
   - Add comprehensive error responses
   - Implement fallback mechanisms
   - Add dead letter queue

**Deliverables:**
- ✅ PDF conversion working via API
- ✅ Main app integrated with service
- ✅ Error handling complete

### Phase 3: Testing & Optimization (Week 5)

#### Tasks:
1. **Load Testing**
   - Test with various PDF sizes
   - Test concurrent uploads
   - Identify bottlenecks

2. **Performance Optimization**
   - Tune worker pool size
   - Optimize image compression
   - Implement caching where appropriate

3. **Integration Testing**
   - End-to-end test suite
   - Failure scenario testing
   - Security testing

**Deliverables:**
- ✅ Load test results
- ✅ Performance benchmarks
- ✅ Test coverage >80%

### Phase 4: Production Deployment (Week 6)

#### Tasks:
1. **Security Hardening**
   - Implement API key rotation
   - Set up WAF rules
   - Configure SSL/TLS

2. **Monitoring Setup**
   - Application metrics
   - Infrastructure metrics
   - Alerting rules

3. **Documentation**
   - API documentation (Swagger/OpenAPI)
   - Runbook for operations
   - Migration guide

**Deliverables:**
- ✅ Production deployment
- ✅ Monitoring dashboards
- ✅ Complete documentation

### Phase 5: Migration (Week 7-8)

#### Tasks:
1. **Gradual Rollout**
   - Enable for 10% of users
   - Monitor for issues
   - Gradually increase to 100%

2. **Deprecate Old System**
   - Monitor usage of old endpoint
   - Send deprecation notices
   - Remove old code

3. **Post-migration Monitoring**
   - Track performance improvements
   - Monitor cost changes
   - Gather user feedback

**Deliverables:**
- ✅ 100% traffic on new system
- ✅ Old system deprecated
- ✅ Post-migration report

---

## Security Considerations

### Authentication & Authorization

#### API Key Management
```python
# PDF Service - API Key Validation
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    
    # Validate against stored keys (Redis or database)
    if not is_valid_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return api_key
```

#### Key Rotation Strategy
- Generate new API keys monthly
- Support multiple active keys during rotation
- Audit log all API key usage
- Revoke compromised keys immediately

### Data Security

#### File Handling
1. **Encryption at Rest**
   - Encrypt temporary files on disk
   - Use encrypted volumes (AWS EBS encryption)

2. **Encryption in Transit**
   - TLS 1.3 for all API communication
   - Certificate pinning for service-to-service

3. **Data Sanitization**
   - Clean up temporary files after processing
   - Implement file retention policies
   - Secure deletion of sensitive data

#### Access Control
```yaml
Network Security:
  - Private VPC for PDF service
  - Security groups limiting inbound traffic
  - No public internet access except via API gateway
  
Rate Limiting:
  - 100 requests per minute per API key
  - 10 concurrent jobs per organization
  - File size limit: 50MB per upload
```

### Compliance

#### HIPAA Considerations (Healthcare Data)
- ✅ PHI data encrypted in transit and at rest
- ✅ Audit logging for all data access
- ✅ Business Associate Agreement (BAA) with cloud provider
- ✅ Regular security audits
- ✅ Automatic data retention and deletion policies

#### SOC 2 Requirements
- ✅ Access controls and authentication
- ✅ Continuous monitoring and alerting
- ✅ Incident response procedures
- ✅ Vendor risk management

---

## Cost Analysis

### Current Architecture (Baseline)

```
Main Application Server:
  Instance: 4 CPU, 8GB RAM
  Cost: $150/month
  
  Issues:
  - PDF processing consumes 30-40% of CPU
  - Memory spikes during concurrent uploads
  - Can't scale independently
```

### Proposed Architecture

#### Development/Staging Environment
```
PDF Processing Service:
  Instance: 2 CPU, 4GB RAM (1 instance)
  Cost: $60/month
  
Background Queue (Redis):
  Instance: 1 CPU, 1GB RAM
  Cost: $15/month
  
Main Application:
  Instance: 2 CPU, 4GB RAM (reduced from 4 CPU)
  Cost: $80/month (savings: $70)
  
Total: $155/month (similar to baseline)
```

#### Production Environment (with autoscaling)
```
PDF Processing Service:
  Base: 2 instances @ $60/month = $120
  Peak: 6 instances @ $60/month = $360
  Average: ~$200/month
  
Background Queue (Redis):
  Instance: 2 CPU, 2GB RAM (HA)
  Cost: $30/month
  
Main Application:
  Base: 2 instances @ $80/month = $160
  Peak: 4 instances @ $80/month = $320
  Average: ~$200/month
  
Load Balancer:
  Cost: $20/month
  
Total Average: $450/month
Total Peak: $730/month
```

### Cost Comparison

| Scenario | Current | Proposed | Difference |
|----------|---------|----------|------------|
| **Dev/Staging** | $150/mo | $155/mo | +$5/mo (+3%) |
| **Production (avg)** | $300/mo* | $450/mo | +$150/mo (+50%) |
| **Production (peak)** | $600/mo* | $730/mo | +$130/mo (+22%) |

*Estimated for comparable performance

### ROI Considerations

#### Cost Savings:
- **Reduced downtime**: Fewer crashes = less lost revenue
- **Faster processing**: Better user experience = higher retention
- **Developer efficiency**: Less time fixing poppler issues
- **Scaling efficiency**: Only scale what you need

#### Break-even Analysis:
```
Additional monthly cost: ~$150
Developer time saved: ~8 hours/month (fixing poppler issues)
Developer hourly rate: $50/hour
Monthly savings: $400

Net savings: $250/month
Annual savings: $3,000
```

---

## Migration Strategy

### Pre-Migration Checklist

#### Infrastructure
- [ ] PDF service deployed to staging
- [ ] Background queue configured
- [ ] Load balancer set up
- [ ] Monitoring and alerting configured
- [ ] API keys generated and secured

#### Application
- [ ] New endpoints implemented
- [ ] Old endpoints marked as deprecated
- [ ] Feature flag implemented
- [ ] Rollback plan documented
- [ ] Integration tests passing

#### Documentation
- [ ] API documentation published
- [ ] Migration runbook created
- [ ] Team trained on new architecture
- [ ] Incident response procedures updated

### Migration Steps

#### Step 1: Parallel Operation (Week 1)
```python
# Main application - dual mode
@router.post("/timesheets/upload")
async def upload_timesheet(file: UploadFile, use_external_service: bool = False):
    if use_external_service or settings.PDF_SERVICE_ENABLED:
        # New: External PDF service
        return await process_via_external_service(file)
    else:
        # Old: In-process conversion
        return await process_in_process(file)
```

**Actions:**
- Enable external service for test accounts only
- Compare results between old and new methods
- Monitor for discrepancies

#### Step 2: Gradual Rollout (Week 2-3)
```python
# Feature flag with percentage rollout
def should_use_external_service(user_id: str) -> bool:
    # Hash user_id to get consistent routing
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    
    # Gradually increase percentage
    rollout_percentage = get_rollout_percentage()  # Start at 10%, increase daily
    
    return (hash_value % 100) < rollout_percentage
```

**Schedule:**
- Day 1-2: 10% of users
- Day 3-4: 25% of users
- Day 5-6: 50% of users
- Day 7-8: 75% of users
- Day 9+: 100% of users

**Monitoring:**
- Track success rates for both methods
- Compare processing times
- Monitor error rates
- Watch for performance degradation

#### Step 3: Full Migration (Week 4)
```python
# Remove old code path
@router.post("/timesheets/upload")
async def upload_timesheet(file: UploadFile):
    # Only use external service
    return await process_via_external_service(file)
```

**Actions:**
- Switch 100% to external service
- Keep old code for 2 weeks as backup
- Monitor closely for issues

#### Step 4: Cleanup (Week 5-6)
```python
# Remove deprecated code completely
# Remove in-process PDF conversion logic
# Remove poppler-utils from main app requirements
```

**Actions:**
- Remove old PDF processing code
- Update documentation
- Archive old code in git history

### Rollback Plan

#### Quick Rollback (< 5 minutes)
```bash
# Revert feature flag
curl -X POST https://api.example.com/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"pdf_external_service": false}'
```

#### Full Rollback (< 30 minutes)
```bash
# Deploy previous version of main application
kubectl rollout undo deployment/main-app

# Disable PDF service traffic at load balancer
kubectl scale deployment/pdf-service --replicas=0
```

#### Criteria for Rollback:
- Error rate > 5%
- Processing time > 2x baseline
- Critical bug discovered
- Service unavailability > 5 minutes

---

## Monitoring & Observability

### Key Metrics

#### PDF Processing Service
```yaml
Performance Metrics:
  - conversion_duration_seconds (histogram)
  - pages_processed_total (counter)
  - active_conversions (gauge)
  - queue_size (gauge)
  
Error Metrics:
  - conversion_errors_total (counter by error_type)
  - timeout_errors_total (counter)
  - memory_errors_total (counter)
  
Resource Metrics:
  - cpu_usage_percent (gauge)
  - memory_usage_bytes (gauge)
  - disk_usage_bytes (gauge)
```

#### Main Application
```yaml
Integration Metrics:
  - pdf_service_requests_total (counter by status)
  - pdf_service_latency_seconds (histogram)
  - pdf_service_failures_total (counter)
  
Business Metrics:
  - timesheet_uploads_total (counter)
  - timesheet_processing_success_rate (gauge)
  - average_processing_time_seconds (gauge)
```

### Alerting Rules

#### Critical Alerts (Page immediately)
```yaml
- name: PDF Service Down
  condition: up{job="pdf-service"} == 0
  duration: 2m
  severity: critical
  
- name: High Error Rate
  condition: rate(conversion_errors_total[5m]) > 0.1
  duration: 5m
  severity: critical
  
- name: Queue Backed Up
  condition: queue_size > 1000
  duration: 10m
  severity: critical
```

#### Warning Alerts (Investigate within 1 hour)
```yaml
- name: Slow Processing
  condition: histogram_quantile(0.95, conversion_duration_seconds) > 60
  duration: 15m
  severity: warning
  
- name: High Memory Usage
  condition: memory_usage_percent > 85
  duration: 10m
  severity: warning
```

### Logging Strategy

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "pdf_conversion_started",
    job_id=job_id,
    filename=filename,
    pages=page_count,
    user_id=user_id,
    organization_id=org_id
)

# Log completion
logger.info(
    "pdf_conversion_completed",
    job_id=job_id,
    duration_ms=duration,
    pages_processed=pages,
    success=True
)

# Log errors with trace
logger.error(
    "pdf_conversion_failed",
    job_id=job_id,
    error=str(error),
    stack_trace=traceback.format_exc(),
    filename=filename
)
```

#### Log Aggregation
- **Tool**: ELK Stack (Elasticsearch, Logstash, Kibana) or AWS CloudWatch
- **Retention**: 30 days for all logs, 90 days for errors
- **Sampling**: 100% errors, 10% info logs in production

### Dashboards

#### Service Health Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  PDF Processing Service - Health                         │
├─────────────────────────────────────────────────────────┤
│  Status: 🟢 Healthy                                      │
│  Uptime: 99.95%                                          │
│  Active Instances: 3                                     │
│                                                          │
│  Current Load:                                           │
│  ├─ Requests/min: 45                                    │
│  ├─ Active Jobs: 12                                     │
│  └─ Queue Size: 3                                       │
│                                                          │
│  Performance (Last 1h):                                  │
│  ├─ P50 Latency: 2.3s                                   │
│  ├─ P95 Latency: 8.1s                                   │
│  ├─ P99 Latency: 15.2s                                  │
│  └─ Success Rate: 99.2%                                 │
└─────────────────────────────────────────────────────────┘
```

#### Business Metrics Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  Timesheet Processing - Business Metrics                 │
├─────────────────────────────────────────────────────────┤
│  Today:                                                  │
│  ├─ Uploads: 1,234                                      │
│  ├─ Processed: 1,189                                    │
│  ├─ Failed: 8                                           │
│  └─ Processing: 37                                      │
│                                                          │
│  Average Times:                                          │
│  ├─ Upload to Processing: 2.1s                          │
│  ├─ Processing Duration: 8.5s                           │
│  └─ Total Time: 10.6s                                   │
│                                                          │
│  Trends (7 days):                                       │
│  ├─ Volume: ↑ 15%                                       │
│  ├─ Success Rate: → 99.1%                               │
│  └─ Avg Duration: ↓ 12%                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Disaster Recovery

### Backup Strategy

#### Data
- PDF files: Not backed up (ephemeral processing)
- Job metadata: Redis snapshots every 5 minutes
- Application data: MongoDB backups every 4 hours

#### Service Recovery
- **RTO** (Recovery Time Objective): 15 minutes
- **RPO** (Recovery Point Objective): 5 minutes

### Failure Scenarios

#### Scenario 1: PDF Service Complete Failure
```
Detection: Health check fails
Time to detect: 30 seconds
Automatic action: Traffic routed to backup instance
Manual action: Investigate root cause, deploy fix
Fallback: Temporarily disable uploads, show maintenance message
Recovery time: 5-15 minutes
```

#### Scenario 2: Queue Service Failure
```
Detection: Queue operations fail
Time to detect: 1 minute
Automatic action: Jobs cached in application memory
Manual action: Restart Redis, replay cached jobs
Fallback: Process in-application (old method)
Recovery time: 5 minutes
```

#### Scenario 3: External OCR API Failure
```
Detection: High error rate from Gemini API
Time to detect: 2 minutes
Automatic action: Retry with exponential backoff
Manual action: Switch to backup OCR provider (if available)
Fallback: Queue jobs for later processing
Recovery time: Dependent on OCR provider
```

---

## Future Enhancements

### Phase 2 Features

#### Advanced OCR
- Multi-language support (Spanish, etc.)
- Handwriting recognition
- Form field detection
- Table extraction

#### Performance
- GPU acceleration for image processing
- Parallel page processing
- Smart caching of frequently uploaded documents
- Predictive scaling based on time-of-day patterns

#### Features
- Batch upload API (process multiple PDFs in one request)
- Webhook support for async notifications
- PDF editing capabilities (rotate, crop, merge)
- Direct integration with cloud storage (S3, Google Drive)

### Phase 3 Features

#### AI/ML Integration
- Document classification (invoice vs timesheet vs contract)
- Anomaly detection (duplicate submissions)
- Quality scoring for extracted data
- Auto-correction of common OCR errors

#### Enterprise Features
- Multi-tenancy with resource quotas
- Custom OCR models per organization
- Advanced analytics and reporting
- SLA guarantees

---

## Conclusion

### Summary

This architecture provides a robust, scalable solution for PDF and OCR processing that:
- ✅ Eliminates the recurring poppler-utils persistence issue
- ✅ Improves performance through async processing and independent scaling
- ✅ Enhances reliability with proper error handling and retry logic
- ✅ Reduces main application resource consumption
- ✅ Provides clear path for future enhancements

### Recommended Next Steps

1. **Immediate** (This Sprint):
   - Review and approve architecture
   - Allocate budget and resources
   - Set up development environment

2. **Short-term** (Next 1-2 Months):
   - Implement Phase 1 (Infrastructure setup)
   - Build and test core features
   - Deploy to staging environment

3. **Medium-term** (3-4 Months):
   - Production deployment
   - Gradual migration of traffic
   - Deprecate old system

4. **Long-term** (6+ Months):
   - Phase 2 and 3 enhancements
   - Scale based on usage patterns
   - Continuous optimization

### Success Criteria

The migration will be considered successful when:
- ✅ 0 poppler-utils related incidents for 30 days
- ✅ 99.5% uptime for PDF processing
- ✅ P95 processing time < 15 seconds
- ✅ Cost per processed page < current baseline
- ✅ Developer time spent on PDF issues reduced by 90%

---

## Appendix

### A. Technology Alternatives

#### PDF Processing Service
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **FastAPI (Python)** | Native integration, team expertise | Slightly slower than compiled languages | ✅ **Recommended** |
| **Node.js + Express** | Very fast, good async | Different language from main app | ⚠️ Consider if performance critical |
| **Go** | Excellent performance, low memory | Learning curve, less PDF libraries | ⚠️ Consider for Phase 2 |

#### Background Queue
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Redis + Celery** | Python-native, feature-rich | Requires Redis management | ✅ **Recommended** |
| **AWS SQS + Lambda** | Serverless, auto-scaling | Vendor lock-in, cold starts | ⚠️ Consider for cloud-native |
| **RabbitMQ** | Enterprise-grade, robust | Complex setup | ⚠️ Overkill for initial phase |

### B. Sample Code

#### PDF Service - Main Application (main.py)
```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime, timezone
import aiofiles
import os
from pdf2image import convert_from_path
from pathlib import Path
import asyncio

app = FastAPI(title="PDF Processing Service", version="1.0.0")

# Configuration
TEMP_DIR = Path("/tmp/pdf_processing")
TEMP_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# In-memory job store (use Redis in production)
jobs = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import subprocess
    try:
        result = subprocess.run(
            ["pdfinfo", "-v"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        poppler_version = result.stderr.split('\n')[0].split()[-1]
        
        return {
            "status": "healthy",
            "poppler_version": poppler_version,
            "service": "pdf-processing",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/api/v1/pdf/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    dpi: int = 200,
    format: str = "jpeg"
):
    """Convert PDF to images"""
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Create job
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "processing",
        "created_at": datetime.now(timezone.utc),
        "filename": file.filename
    }
    jobs[job_id] = job
    
    # Save file temporarily
    temp_file = TEMP_DIR / f"{job_id}.pdf"
    async with aiofiles.open(temp_file, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Process in background
    asyncio.create_task(process_pdf(job_id, str(temp_file), dpi, format))
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "PDF conversion started"
    }

async def process_pdf(job_id: str, file_path: str, dpi: int, format: str):
    """Background task to process PDF"""
    try:
        # Convert PDF to images
        images = convert_from_path(file_path, dpi=dpi, fmt=format)
        
        # Save images
        result_urls = []
        for i, image in enumerate(images):
            image_path = TEMP_DIR / f"{job_id}_page_{i+1}.{format}"
            image.save(image_path, format.upper())
            result_urls.append(f"/images/{job_id}_page_{i+1}.{format}")
        
        # Update job
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = result_urls
        jobs[job_id]["pages"] = len(images)
        jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
    finally:
        # Cleanup
        Path(file_path).unlink(missing_ok=True)

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    return jobs[job_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### C. Cost Calculator

Use this spreadsheet to estimate costs for your specific usage:

```
Usage Inputs:
- Daily PDF uploads: [500]
- Average pages per PDF: [5]
- Peak hour uploads (% of daily): [30%]
- Required uptime SLA: [99.5%]

Calculated Outputs:
- Monthly API calls: 15,000
- Peak requests per hour: 225
- Required instances (peak): 3
- Estimated monthly cost: $240

Breakdown:
- Compute (PDF service): $180
- Queue (Redis): $30
- Load balancer: $20
- Data transfer: $10
```

### D. Glossary

**API Gateway**: Entry point that routes requests to appropriate services
**Async Processing**: Non-blocking operations that don't wait for completion
**Background Queue**: System for managing and executing jobs asynchronously
**Dead Letter Queue**: Storage for failed jobs that can't be processed
**Webhook**: HTTP callback for event notifications
**OCR**: Optical Character Recognition - converting images to text
**SLA**: Service Level Agreement - guaranteed uptime/performance
**RTO**: Recovery Time Objective - max acceptable downtime
**RPO**: Recovery Point Objective - max acceptable data loss

---

**Document Version**: 1.0
**Last Updated**: 2024-12-15
**Author**: E1 Development Agent
**Status**: Approved for Implementation

