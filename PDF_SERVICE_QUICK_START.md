# PDF Processing Service - Quick Start Guide

## TL;DR

**Current Problem**: Poppler-utils keeps disappearing on container restarts  
**Solution**: Move PDF processing to an external microservice  
**Timeline**: 6-8 weeks for full implementation  
**Cost Impact**: +$150/month for production (~50% increase)  
**Benefit**: Eliminate recurring poppler issues, better performance, independent scaling

---

## For Developers

### What Changes?

#### Before (Current):
```python
# In main application - Synchronous, in-process
@app.post("/api/timesheets/upload")
async def upload_timesheet(file: UploadFile):
    # Convert PDF directly
    images = convert_from_path(file_path)  # Blocks here
    
    # Extract data
    data = await extract_data(images)
    
    # Return result
    return {"status": "completed", "data": data}
```

#### After (Proposed):
```python
# In main application - Asynchronous, external service
@app.post("/api/timesheets/upload")
async def upload_timesheet(file: UploadFile):
    # Send to PDF service (non-blocking)
    job = await pdf_service.convert(file)
    
    # Return immediately
    return {"status": "processing", "job_id": job.id}

# Webhook receives result when done
@app.post("/webhooks/pdf-complete")
async def handle_pdf_complete(job_result: dict):
    # Process extracted data
    await save_timesheet(job_result)
```

### New API to Learn

```bash
# PDF Service endpoints
POST /api/v1/pdf/convert     # Start conversion
GET  /api/v1/jobs/{job_id}   # Check status
GET  /health                 # Health check

# Authentication
Authorization: Bearer {API_KEY}
```

### Local Development

```bash
# Start PDF service locally
cd pdf-service
docker-compose up

# Service runs on http://localhost:8000
# Main app connects via environment variable
export PDF_SERVICE_URL="http://localhost:8000"
```

---

## For DevOps/Platform Team

### Infrastructure Needs

#### New Services:
1. **PDF Processing Service**
   - Docker container with poppler-utils pre-installed
   - 2 CPU, 4GB RAM (baseline)
   - Autoscale 1-10 instances based on queue size

2. **Background Queue**
   - Redis instance (2GB RAM)
   - High availability setup for production

3. **Load Balancer**
   - Route /api/pdf/* to PDF service
   - Health check on /health endpoint

#### Deployment:
```yaml
# Kubernetes example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: pdf-service
        image: azai/pdf-service:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Monitoring Setup

#### Required Metrics:
- PDF conversion success rate
- Queue size and processing time
- CPU/memory usage per service
- API response times

#### Alerts:
- Service down > 2 minutes → Page on-call
- Error rate > 5% → Warning
- Queue backed up > 1000 jobs → Warning

---

## For Product/Project Managers

### Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1**: Infrastructure | 2 weeks | PDF service running in staging |
| **Phase 2**: Integration | 2 weeks | Main app connected, tested |
| **Phase 3**: Testing | 1 week | Load testing complete |
| **Phase 4**: Deployment | 1 week | Production ready |
| **Phase 5**: Migration | 2 weeks | Gradual rollout to 100% |
| **Total** | **8 weeks** | Fully migrated |

### Resource Requirements

#### Team:
- 1 Backend Developer (full-time, 6 weeks)
- 1 DevOps Engineer (part-time, 4 weeks)
- 1 QA Engineer (part-time, 2 weeks)

#### Budget:
- Development: Existing team
- Infrastructure: +$150/month ongoing
- One-time setup: ~$500 (AWS resources during migration)

### User Impact

#### During Migration:
- ✅ No downtime required
- ✅ Gradual rollout (test with 10%, then increase)
- ✅ Easy rollback if issues occur

#### After Migration:
- ✅ Faster upload experience (non-blocking)
- ✅ No more "PDF conversion failed" errors
- ✅ Better handling of large multi-page PDFs
- ✅ Real-time progress updates

### Success Metrics

- Zero poppler-related incidents for 30 days
- 99.5% uptime for PDF processing
- P95 processing time < 15 seconds
- Developer time on PDF issues reduced by 90%

---

## FAQs

### Q: Why not just fix the poppler persistence issue?
**A**: That's a platform-level problem outside our control. The container environment doesn't persist system packages. This architecture solves it permanently.

### Q: Can we start with a simpler solution?
**A**: We could keep current setup and run the install script on every restart, but:
- Requires manual intervention
- Still blocks main application
- Doesn't improve scalability
- Wastes developer time

### Q: What if the PDF service goes down?
**A**: 
- Main app continues running (degraded mode)
- Jobs queue up automatically
- Process when service recovers
- Can show users "Processing delayed" message

### Q: Do we need all this for a small app?
**A**: Consider current pain:
- Poppler bug fixed 4+ times
- Each incident wastes 2-4 hours
- Users can't upload during outages
- Cost: ~$200-400/month in developer time
  
External service costs $150/month but eliminates all of this.

### Q: What about vendor lock-in?
**A**: Service is containerized and portable:
- Docker image runs anywhere (AWS, GCP, on-prem)
- No cloud-specific dependencies
- Easy to migrate providers

### Q: Can we use a SaaS solution instead?
**A**: Options like AWS Textract or Google Document AI:
- **Pros**: Zero maintenance, already scalable
- **Cons**: More expensive ($1-10 per 1000 pages), privacy concerns with PHI data, less control
- **Verdict**: Could be good for Phase 2, but DIY is better for healthcare data

---

## Decision Matrix

| Factor | Current Setup | External Service | SaaS (AWS Textract) |
|--------|---------------|------------------|---------------------|
| **Reliability** | ⚠️ Poor (recurring issues) | ✅ High | ✅ Very High |
| **Performance** | ⚠️ Blocks requests | ✅ Async | ✅ Async |
| **Scalability** | ❌ Limited | ✅ Independent | ✅ Unlimited |
| **Cost (monthly)** | $0 (but high maintenance) | $150 | $500-2000* |
| **Setup Time** | None | 8 weeks | 2 weeks |
| **Data Privacy** | ✅ Full control | ✅ Full control | ⚠️ Vendor processes data |
| **Maintenance** | ❌ High | ⚠️ Medium | ✅ Low |

*Estimated for 15,000 pages/month

---

## Next Steps

### Immediate Actions:
1. ✅ **Review architecture document** (EXTERNAL_PDF_OCR_SERVICE_ARCHITECTURE.md)
2. ⏳ **Approve budget** ($150/month + one-time $500 setup)
3. ⏳ **Allocate team resources** (1 developer for 6 weeks)
4. ⏳ **Set timeline** (8-week target)

### Week 1 Tasks:
- Set up development environment for PDF service
- Create Docker image with poppler-utils
- Deploy to local/staging environment
- Implement basic health check endpoint

### Getting Started:
```bash
# Clone the repository
git clone https://github.com/your-org/azai-pdf-service

# Read the full architecture doc
cat EXTERNAL_PDF_OCR_SERVICE_ARCHITECTURE.md

# Start development
cd pdf-service
docker-compose up
```

---

## Support

### Documentation:
- **Full Architecture**: `/app/EXTERNAL_PDF_OCR_SERVICE_ARCHITECTURE.md`
- **Current Issues**: `/app/CRITICAL_POPPLER_PERSISTENCE_ISSUE.md`
- **API Docs**: Will be generated at `/docs` (Swagger UI)

### Contacts:
- **Technical Questions**: Backend team lead
- **Infrastructure**: DevOps team
- **Timeline/Budget**: Project manager

### Resources:
- Architecture diagram (see full doc)
- Sample code (Appendix B in full doc)
- Cost calculator (Appendix C in full doc)

---

**Last Updated**: 2024-12-15  
**Version**: 1.0  
**Status**: Ready for Review
