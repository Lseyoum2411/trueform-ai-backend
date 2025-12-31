# Step 1: Backend Setup Commands

## Windows (PowerShell):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
mkdir uploads, results
uvicorn app.main:app --reload --port 8000
```

## Linux/Mac:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p uploads results
uvicorn app.main:app --reload --port 8000
```

## Test Commands (after server starts):

### Health Check:
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy"}`

### Get Sports:
```bash
curl http://localhost:8000/api/v1/sports
```
Expected: JSON array with 3 sports (basketball, golf, weightlifting) + exercise types

### Upload Test (create test.mp4 first or use existing):
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "video=@test.mp4" \
  -F "sport=basketball" \
  -F "exercise_type=jumpshot"
```
Expected: `{"video_id":"...", "status":"queued", ...}`








