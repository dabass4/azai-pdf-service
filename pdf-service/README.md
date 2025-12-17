# PDF Processing Service

External microservice for PDF to image conversion using poppler-utils.

## Features

- ✅ PDF to image conversion
- ✅ PDF metadata extraction
- ✅ API key authentication
- ✅ Health check endpoint
- ✅ CORS enabled
- ✅ Base64 image encoding

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
PDF_SERVICE_API_KEY=your-secret-key uvicorn main:app --reload
```

## Deploy to Railway

1. Push this repo to GitHub
2. Connect to Railway.app
3. Set environment variable: `PDF_SERVICE_API_KEY`
4. Deploy automatically

## API Endpoints

### Health Check
```bash
curl https://your-service.railway.app/health
```

### Convert PDF
```bash
curl -X POST https://your-service.railway.app/api/v1/pdf/convert \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test.pdf" \
  -F "dpi=200"
```

### Get Metadata
```bash
curl -X POST https://your-service.railway.app/api/v1/pdf/metadata \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test.pdf"
```

## Environment Variables

- `PDF_SERVICE_API_KEY` - API key for authentication (required)
- `PORT` - Port to run on (default: 8000)

## Security

- API key authentication required
- 50MB file size limit
- CORS configured (update for production)
- Input validation on all endpoints