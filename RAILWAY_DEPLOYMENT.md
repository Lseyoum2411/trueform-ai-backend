# Railway Deployment Configuration

## Files Created/Updated

1. **runtime.txt** - Pins Python 3.10.11 for Railway
2. **Procfile** - Defines start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **requirements.txt** - Clean production dependencies (Python 3.10 compatible)

## Railway Configuration

### Environment Variables (Set in Railway Dashboard)

```
CORS_ORIGINS=https://your-frontend-url.vercel.app
UPLOAD_DIR=/tmp/uploads
RESULTS_DIR=/tmp/results
MAX_UPLOAD_SIZE_MB=100
MAX_VIDEO_DURATION_SEC=60
```

### Start Command

Railway will automatically use the `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Build Command

Railway will automatically:
1. Detect Python from `runtime.txt`
2. Run `pip install -r requirements.txt`
3. Start using `Procfile`

## Verification

- ✅ Python 3.10.11 installed and verified
- ✅ All dependencies installed (MediaPipe 0.10.21 compatible)
- ✅ Backend imports successfully
- ✅ Procfile configured for Railway
- ✅ runtime.txt pins Python 3.10

## Next Steps

1. Push code to GitHub
2. Connect repository in Railway
3. Set environment variables
4. Deploy





