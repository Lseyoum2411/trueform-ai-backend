# TrueForm AI Backend

FastAPI backend for AI-powered sports form analysis using pose estimation and biomechanics.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Quick Demo

### 1. Try the Demo Endpoint (No Upload Required)

Get example responses instantly:

```bash
curl http://localhost:8000/api/v1/demo
```

Returns sample upload, status, and results responses. Perfect for frontend development and demos!

### 2. Upload a Video

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "video=@your_video.mp4" \
  -F "sport=basketball"
```

Response includes `video_id` and `next_poll_url` for status polling.

### 3. Check Status

```bash
curl "http://localhost:8000/api/v1/upload/status/{video_id}"
```

Poll until `status` is `"completed"`.

### 4. Get Results

```bash
curl "http://localhost:8000/api/v1/upload/results/{video_id}"
```

Returns analysis results with scores, feedback, and improvement suggestions.

---

## Frontend Integration Example

```javascript
// 1. Upload video
const formData = new FormData();
formData.append('video', fileInput.files[0]);
formData.append('sport', 'basketball');

const uploadResponse = await fetch('http://localhost:8000/api/v1/upload', {
  method: 'POST',
  body: formData
});

const { video_id, next_poll_url } = await uploadResponse.json();

// 2. Poll status
const pollStatus = async () => {
  const statusResponse = await fetch(next_poll_url);
  const status = await statusResponse.json();
  
  if (status.status === 'completed') {
    // 3. Get results
    const resultsResponse = await fetch(
      `http://localhost:8000/api/v1/upload/results/${video_id}`
    );
    const results = await resultsResponse.json();
    console.log('Analysis Score:', results.overall_score);
  } else if (status.status === 'error') {
    console.error('Analysis failed:', status.error);
  } else {
    // Still processing, poll again
    setTimeout(pollStatus, 2000);
  }
};

pollStatus();
```

---

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Health check |
| `/api/v1/demo` | GET | Get example responses (no ML, no files) |
| `/api/v1/sports` | GET | List supported sports |
| `/api/v1/upload` | POST | Upload video for analysis |
| `/api/v1/upload/status/{video_id}` | GET | Check analysis status |
| `/api/v1/upload/results/{video_id}` | GET | Get analysis results |

---

## Features

- ✅ **Lazy ML Loading** - Models load only when needed, not at startup
- ✅ **Background Processing** - Non-blocking video analysis
- ✅ **Rate Limiting** - Prevents system overload (max 3 concurrent)
- ✅ **Request Correlation** - Request IDs in logs and responses
- ✅ **Structured Errors** - Consistent error format with error codes
- ✅ **Demo Mode** - Instant example responses without processing

---

## Supported Sports

- **Basketball** - Jump shot form analysis
- **Golf** - Swing mechanics (driver, iron, chip, putt)
- **Weightlifting** - Form analysis for 7 different lifts

---

## Deployment

See `RAILWAY_DEPLOY_INSTRUCTIONS.md` for Railway deployment details.

---

## API Contract

See `FRONTEND_CONTRACT.md` for complete API documentation and frontend integration guide.

---

## Requirements

- Python 3.10+
- OpenCV (headless)
- MediaPipe
- FastAPI
- See `requirements.txt` for full list




