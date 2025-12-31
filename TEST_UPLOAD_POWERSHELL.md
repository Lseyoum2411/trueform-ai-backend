# PowerShell Upload Test Commands

## Domain
```
https://trueform-ai-backend-production.up.railway.app
```

## Why GET Returns 405
The `/api/v1/upload` endpoint only accepts POST requests (for file uploads). GET requests return "405 Method Not Allowed" because GET is not implemented for this endpoint.

---

## Test 1: Upload Basketball Video (Simplest - no exercise_type needed)

```powershell
# Set variables
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\your\video.mp4"  # Replace with actual path

# Upload video for basketball analysis
# IMPORTANT: Field name "video" must match the FastAPI parameter name exactly
$form = @{
    video = Get-Item -Path $filePath  # ← Must be "video", NOT "file"
    sport = "basketball"
}

try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form -ErrorAction Stop
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($jsonResponse.video_id)" -ForegroundColor Cyan
    Write-Host "Status: $($jsonResponse.status)" -ForegroundColor Cyan
    Write-Host "Full response:" -ForegroundColor Yellow
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

---

## Test 2: Upload Golf Video (Requires exercise_type)

```powershell
# Set variables
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\your\golf_video.mp4"  # Replace with actual path

# Upload video for golf analysis (driver)
$form = @{
    video = Get-Item -Path $filePath
    sport = "golf"
    exercise_type = "driver"  # Options: "driver", "iron", "chip", "putt"
}

try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form -ErrorAction Stop
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($jsonResponse.video_id)" -ForegroundColor Cyan
    $jsonResponse | ConvertTo-Json -Depth 10
    
    $videoId = $jsonResponse.video_id
} catch {
    Write-Host "❌ Upload failed!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
```

---

## Test 3: Upload Weightlifting Video (Requires exercise_type)

```powershell
# Set variables
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\your\squat_video.mp4"  # Replace with actual path

# Upload video for weightlifting analysis (back_squat)
$form = @{
    video = Get-Item -Path $filePath
    sport = "weightlifting"
    exercise_type = "back_squat"  # Options: "back_squat", "front_squat", "deadlift", "rdl", "bench_press", "barbell_row", "lat_pulldown"
}

try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form -ErrorAction Stop
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($jsonResponse.video_id)" -ForegroundColor Cyan
    $jsonResponse | ConvertTo-Json -Depth 10
    
    $videoId = $jsonResponse.video_id
} catch {
    Write-Host "❌ Upload failed!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
```

---

## Check Upload Status

After uploading, poll the status endpoint:

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

## Get Analysis Results

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

## Expected Success Response

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000.mp4",
  "sport": "basketball",
  "exercise_type": "jumpshot",
  "lift_type": null,
  "uploaded_at": "2025-12-19T12:00:00",
  "file_size": 5242880,
  "duration": 5.5,
  "status": "queued"
}
```

---

## Error Responses Explained

| Status Code | Meaning | Cause |
|-------------|---------|-------|
| **400** | Bad Request | Invalid sport, missing exercise_type for golf/weightlifting, invalid exercise_type, video duration too long |
| **405** | Method Not Allowed | Using GET instead of POST (expected behavior) |
| **413** | Payload Too Large | File size exceeds 100MB limit |
| **422** | Unprocessable Entity | Invalid file format or missing required fields |
| **500** | Internal Server Error | Server-side processing error |

---

## Lazy ML Loading Verification

After upload, check Railway logs for:

1. **Initial upload** - Should show minimal logs, NO ML model initialization
2. **During processing** - Should see:
   ```
   → Request: POST /api/v1/upload
   ← Response: 200
   → Request: GET /api/v1/upload/status/...
   ```
3. **ML initialization** - Should see logs like:
   ```
   PoseEstimator loaded
   BasketballAnalyzer loaded (or GolfAnalyzer/WeightliftingAnalyzer)
   ```
   These should appear ONLY when analysis starts, NOT at app startup.

4. **No startup blocking** - Health checks should still respond instantly even while analysis is running.

---

## Quick Test Using Existing Uploads Directory

If you have a video in the local `uploads` directory:

```powershell
# Find a video file in uploads
$videoFile = Get-ChildItem -Path "uploads" -Filter "*.mp4" | Select-Object -First 1

if ($videoFile) {
    $uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
    $form = @{
        video = $videoFile
        sport = "basketball"
    }
    
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} else {
    Write-Host "No video files found in uploads directory" -ForegroundColor Yellow
}
```

