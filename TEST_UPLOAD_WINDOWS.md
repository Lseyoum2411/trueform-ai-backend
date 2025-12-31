# Windows Upload Testing Guide

## ⚠️ Important: Windows Shell Limitations

**Windows CMD `curl` is unreliable for multipart file uploads.** The backend correctly validates required fields, but CMD curl often fails to properly format multipart requests, resulting in 422 validation errors.

**Recommended testing methods (in order of reliability):**
1. ✅ **Swagger UI** (`/docs`) - Safest and most reliable
2. ✅ **PowerShell `Invoke-WebRequest`** - Recommended for command-line testing
3. ❌ **CMD `curl`** - Unreliable, may fail silently or produce validation errors

---

## ✅ Method 1: Swagger UI (Recommended for Testing)

### Steps

1. Navigate to: `https://trueform-ai-backend-production.up.railway.app/docs`
2. Find the `POST /api/v1/upload` endpoint
3. Click "Try it out"
4. Fill in the form:
   - **video**: Click "Choose File" and select your video file
   - **sport**: Enter `basketball`, `golf`, or `weightlifting`
   - **exercise_type**: Required for `golf` and `weightlifting`:
     - Golf: `driver`, `iron`, `chip`, `putt`
     - Weightlifting: `back_squat`, `front_squat`, `deadlift`, `rdl`, `bench_press`, `barbell_row`, `lat_pulldown`
5. Click "Execute"

### Advantages

- Visual interface
- Shows exact request format
- Automatic multipart formatting
- Real-time response display
- No shell syntax issues

---

## ✅ Method 2: PowerShell (Recommended for CLI Testing)

### Canonical PowerShell Upload Command

```powershell
# Set variables
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\Users\lksey\Downloads\example.mp4"  # Replace with your video path

# Create form data
# IMPORTANT: Field name "video" must match FastAPI parameter name exactly
$form = @{
    video = Get-Item -Path $filePath  # ← Must be "video", NOT "file"
    sport = "golf"
    exercise_type = "driver"
}

# Upload video
try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form -ErrorAction Stop
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($jsonResponse.video_id)" -ForegroundColor Cyan
    Write-Host "Status: $($jsonResponse.status)" -ForegroundColor Cyan
    
    # Display full response
    $jsonResponse | ConvertTo-Json -Depth 10
    
    # Save video_id for status checking
    $videoId = $jsonResponse.video_id
} catch {
    Write-Host "❌ Upload failed!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}
```

### Example: Basketball (No exercise_type needed)

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\basketball_video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "basketball"
    # exercise_type not needed for basketball (auto-set to "jumpshot")
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Example: Golf

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\golf_video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "golf"
    exercise_type = "driver"  # Options: "driver", "iron", "chip", "putt"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Example: Weightlifting

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\squat_video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "weightlifting"
    exercise_type = "back_squat"  # Options: "back_squat", "front_squat", "deadlift", "rdl", "bench_press", "barbell_row", "lat_pulldown"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## ❌ Method 3: CMD curl (NOT RECOMMENDED)

### Why CMD curl Fails

Windows CMD `curl` has known issues with multipart form data:
- Incorrect boundary handling
- Path escaping problems
- Silent failures or incomplete requests
- Result: 422 validation errors even when syntax looks correct

### Example of Problematic Command

```cmd
REM This often fails on Windows CMD:
curl -X POST "https://trueform-ai-backend-production.up.railway.app/api/v1/upload" ^
  -F "video=@C:\Users\...\video.mp4" ^
  -F "sport=golf" ^
  -F "exercise_type=driver"
```

**Result:** 422 Unprocessable Entity - `{"loc":["body","video"],"msg":"Field required"}`

**Cause:** CMD curl failed to properly include the file in the multipart request, so FastAPI correctly reports the field as missing.

### If You Must Use curl

Use **Git Bash** or **WSL** (not Windows CMD):

```bash
# Git Bash / WSL syntax (Unix-style)
curl -X POST "https://trueform-ai-backend-production.up.railway.app/api/v1/upload" \
  -F "video=@/mnt/c/Users/.../video.mp4" \
  -F "sport=golf" \
  -F "exercise_type=driver"
```

---

## Expected Success Response

After a successful upload, you should receive:

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000.mp4",
  "sport": "golf",
  "exercise_type": "driver",
  "lift_type": null,
  "uploaded_at": "2025-12-23T12:00:00",
  "file_size": 2921659,
  "duration": 12.5,
  "status": "queued"
}
```

### Response Fields Explained

- **video_id**: Unique identifier for the uploaded video
- **filename**: Generated filename (video_id + extension)
- **sport**: The sport type you specified
- **exercise_type**: The exercise type you specified (or auto-set for basketball)
- **lift_type**: Same as exercise_type for weightlifting, null otherwise
- **uploaded_at**: Timestamp when upload completed
- **file_size**: Size in bytes
- **duration**: Video duration in seconds
- **status**: Current processing status (`queued`, `processing`, `completed`, `error`)

---

## Common Error: 422 Missing Video Field

### Error Message

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "video"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### What This Means

**This is a CLIENT-SIDE multipart formatting issue, NOT a backend bug.**

FastAPI correctly validates that the required `video` field is missing from the request. This happens when:

1. **CMD curl fails** to properly format the multipart request
2. **Field name mismatch** - Using `file` instead of `video`
3. **File path issues** - Path not found or not properly escaped
4. **Incomplete request** - Request was interrupted before completion

### Solutions

1. ✅ Use **PowerShell `Invoke-WebRequest`** instead of CMD curl
2. ✅ Use **Swagger UI** for testing
3. ✅ Verify field name is `video` (not `file`)
4. ✅ Check file path exists and is accessible
5. ✅ Use Git Bash/WSL if you must use curl

---

## Checking Upload Status

After upload, poll the status endpoint:

```powershell
$videoId = "your-video-id-here"  # From upload response
$statusUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/status/$videoId"

do {
    try {
        $statusResponse = Invoke-RestMethod -Uri $statusUri -Method Get
        Write-Host "Status: $($statusResponse.status) | Progress: $($statusResponse.progress)%" -ForegroundColor Cyan
        
        if ($statusResponse.status -eq "completed") {
            Write-Host "✅ Analysis complete!" -ForegroundColor Green
            break
        } elseif ($statusResponse.status -eq "error") {
            Write-Host "❌ Analysis failed: $($statusResponse.error)" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "Error checking status: $_" -ForegroundColor Red
        break
    }
} while ($true)
```

---

## Getting Analysis Results

Once status is "completed":

```powershell
$videoId = "your-video-id-here"
$resultsUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/results/$videoId"

try {
    $results = Invoke-RestMethod -Uri $resultsUri -Method Get
    Write-Host "✅ Results retrieved!" -ForegroundColor Green
    $results | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Failed to get results: $_" -ForegroundColor Red
}
```

---

## Quick Reference: FastAPI Field Names

The backend endpoint signature is:

```python
async def upload_video(
    video: UploadFile = File(...),      # ← Field name must be "video"
    sport: str = Form(...),              # ← Field name must be "sport"
    exercise_type: Optional[str] = Form(None),  # ← Field name must be "exercise_type"
):
```

**Critical:** Form field names must EXACTLY match parameter names (case-sensitive).

---

## Troubleshooting Checklist

- [ ] Using PowerShell (not CMD curl) ✅
- [ ] Field name is `video` (not `file`) ✅
- [ ] File path exists and is accessible ✅
- [ ] File size < 100MB ✅
- [ ] Video duration < 60 seconds ✅
- [ ] Sport is one of: `basketball`, `golf`, `weightlifting` ✅
- [ ] `exercise_type` provided for `golf` and `weightlifting` ✅
- [ ] Valid `exercise_type` for the selected sport ✅

---

## Summary

**Backend is correct** - validation works as designed.

**Windows CMD curl is unreliable** - use PowerShell or Swagger UI instead.

**422 "Field required" errors** = client-side multipart formatting issue, not backend bug.

**Recommended:** Always use Swagger UI (`/docs`) for initial testing, then PowerShell for automation.


<<<<<<< HEAD


=======
>>>>>>> 3cec07eb73eb7a9d41527c45e27aa974b9b882ec
