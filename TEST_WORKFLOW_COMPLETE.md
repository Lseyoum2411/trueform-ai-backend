# End-to-End Video Analysis Workflow Test Guide

## Overview

This guide documents the complete workflow from video upload to analysis results retrieval. The workflow consists of three main steps:

1. **Upload** - POST video file
2. **Status Check** - Poll processing status  
3. **Results** - Retrieve analysis results

---

## Prerequisites

- Backend deployed and healthy: `https://trueform-ai-backend-production.up.railway.app`
- Video file (< 100MB, < 60 seconds)
- PowerShell (recommended) or Swagger UI

---

## Step 1: Upload Video

### PowerShell Command

```powershell
# Set variables
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\your\video.mp4"  # Replace with your video path

# Upload video (basketball example - simplest)
$form = @{
    video = Get-Item -Path $filePath
    sport = "basketball"
    # exercise_type not needed for basketball (auto-set to "jumpshot")
}

try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Form $form -ErrorAction Stop
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($jsonResponse.video_id)" -ForegroundColor Cyan
    
    # Save video_id for next steps
    $videoId = $jsonResponse.video_id
    
    # Display full response
    $jsonResponse | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Upload failed!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
```

### Golf Example (requires exercise_type)

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\golf_video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "golf"
    exercise_type = "driver"  # Options: "driver", "iron", "chip", "putt"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$videoId = ($response.Content | ConvertFrom-Json).video_id
Write-Host "Video ID: $videoId"
```

### Weightlifting Example (requires exercise_type)

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\squat_video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "weightlifting"
    exercise_type = "back_squat"  # Options: "back_squat", "front_squat", "deadlift", "rdl", "bench_press", "barbell_row", "lat_pulldown"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$videoId = ($response.Content | ConvertFrom-Json).video_id
Write-Host "Video ID: $videoId"
```

### Swagger UI Method

1. Navigate to: `https://trueform-ai-backend-production.up.railway.app/docs`
2. Find `POST /api/v1/upload`
3. Click "Try it out"
4. Fill form fields:
   - **video**: Choose file
   - **sport**: Enter `basketball`, `golf`, or `weightlifting`
   - **exercise_type**: Required for `golf` and `weightlifting`
5. Click "Execute"
6. Copy the `video_id` from the response

### Expected Response

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000.mp4",
  "sport": "basketball",
  "exercise_type": "jumpshot",
  "lift_type": null,
  "uploaded_at": "2025-12-23T12:00:00",
  "file_size": 5242880,
  "duration": 5.5,
  "status": "queued"
}
```

**Note:** Upload returns immediately with `status: "queued"`. Analysis runs in the background.

---

## Step 2: Check Processing Status

### PowerShell Command (Polling)

```powershell
$videoId = "your-video-id-here"  # From Step 1
$statusUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/status/$videoId"

Write-Host "Polling status for video_id: $videoId" -ForegroundColor Cyan

do {
    try {
        $statusResponse = Invoke-RestMethod -Uri $statusUri -Method Get -ErrorAction Stop
        $status = $statusResponse.status
        $progress = $statusResponse.progress
        
        Write-Host "[$status] Progress: $progress%" -ForegroundColor $(if ($status -eq "completed") {"Green"} elseif ($status -eq "error") {"Red"} else {"Yellow"})
        
        if ($statusResponse.error) {
            Write-Host "Error: $($statusResponse.error)" -ForegroundColor Red
        }
        
        if ($status -eq "completed") {
            Write-Host "✅ Analysis completed!" -ForegroundColor Green
            if ($statusResponse.analysis_id) {
                Write-Host "Analysis ID: $($statusResponse.analysis_id)" -ForegroundColor Cyan
            }
            break
        } elseif ($status -eq "error") {
            Write-Host "❌ Analysis failed!" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 2
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            Write-Host "❌ Video not found. Check video_id." -ForegroundColor Red
        } else {
            Write-Host "Error checking status: $_" -ForegroundColor Red
        }
        break
    }
} while ($true)
```

### Single Status Check

```powershell
$videoId = "your-video-id-here"
$statusUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/status/$videoId"

$status = Invoke-RestMethod -Uri $statusUri -Method Get
$status | ConvertTo-Json -Depth 10
```

### Swagger UI Method

1. Navigate to: `https://trueform-ai-backend-production.up.railway.app/docs`
2. Find `GET /api/v1/upload/status/{video_id}`
3. Click "Try it out"
4. Enter `video_id` from Step 1
5. Click "Execute"

### Expected Responses

**Status: queued**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "progress": 0.0,
  "analysis_id": null,
  "error": null
}
```

**Status: processing**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 60.0,
  "analysis_id": null,
  "error": null
}
```

**Status: completed**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100.0,
  "analysis_id": "abc123-def456-ghi789",
  "error": null
}
```

**Status: error**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "error",
  "progress": 0.0,
  "analysis_id": null,
  "error": "No pose data extracted from video. Ensure person is visible and video is valid."
}
```

---

## Step 3: Retrieve Analysis Results

**Prerequisite:** Status must be `completed` before retrieving results.

### PowerShell Command

```powershell
$videoId = "your-video-id-here"  # From Step 1
$resultsUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/results/$videoId"

try {
    $results = Invoke-RestMethod -Uri $resultsUri -Method Get -ErrorAction Stop
    Write-Host "✅ Results retrieved!" -ForegroundColor Green
    
    # Display key metrics
    Write-Host "`n=== Analysis Summary ===" -ForegroundColor Cyan
    Write-Host "Sport: $($results.sport)" -ForegroundColor White
    Write-Host "Exercise Type: $($results.exercise_type)" -ForegroundColor White
    Write-Host "Overall Score: $($results.overall_score)" -ForegroundColor Yellow
    Write-Host "Frames Analyzed: $($results.frames_analyzed)" -ForegroundColor White
    Write-Host "Processing Time: $($results.processing_time)s" -ForegroundColor White
    
    # Display full results
    Write-Host "`n=== Full Results ===" -ForegroundColor Cyan
    $results | ConvertTo-Json -Depth 10
    
    # Optionally save to file
    $results | ConvertTo-Json -Depth 10 | Out-File -FilePath "results_$videoId.json"
    Write-Host "`nResults saved to: results_$videoId.json" -ForegroundColor Green
    
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "❌ Results not found. Status may still be 'processing' or 'queued'." -ForegroundColor Red
        Write-Host "Check status first: GET /api/v1/upload/status/$videoId" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Failed to get results: $_" -ForegroundColor Red
    }
}
```

### Swagger UI Method

1. Navigate to: `https://trueform-ai-backend-production.up.railway.app/docs`
2. Find `GET /api/v1/upload/results/{video_id}`
3. Click "Try it out"
4. Enter `video_id` from Step 1
5. Click "Execute"

### Expected Response Structure

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_id": "abc123-def456-ghi789",
  "sport": "basketball",
  "exercise_type": "jumpshot",
  "overall_score": 85.5,
  "scores": {
    "stability": 90.0,
    "alignment": 85.0,
    "rhythm": 82.0
  },
  "feedback": [
    {
      "category": "form_analysis",
      "aspect": "stability",
      "message": "Good base stability throughout the shot",
      "severity": "info"
    }
  ],
  "strengths": ["Excellent follow-through", "Good balance"],
  "weaknesses": ["Slight forward lean", "Timing could improve"],
  "frames_analyzed": 150,
  "processing_time": 12.5,
  "analyzed_at": "2025-12-23T12:05:30"
}
```

---

## Complete Workflow Example (All Steps)

```powershell
# Step 1: Upload
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\path\to\video.mp4"

$form = @{
    video = Get-Item -Path $filePath
    sport = "basketball"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$videoId = ($response.Content | ConvertFrom-Json).video_id
Write-Host "✅ Uploaded! Video ID: $videoId" -ForegroundColor Green

# Step 2: Poll Status
$statusUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/status/$videoId"
Write-Host "`n⏳ Waiting for analysis..." -ForegroundColor Yellow

do {
    Start-Sleep -Seconds 3
    $status = Invoke-RestMethod -Uri $statusUri -Method Get
    Write-Host "[$($status.status)] Progress: $($status.progress)%" -ForegroundColor Cyan
    
    if ($status.status -eq "completed") {
        Write-Host "✅ Analysis complete!" -ForegroundColor Green
        break
    } elseif ($status.status -eq "error") {
        Write-Host "❌ Analysis failed: $($status.error)" -ForegroundColor Red
        exit 1
    }
} while ($true)

# Step 3: Get Results
$resultsUri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload/results/$videoId"
$results = Invoke-RestMethod -Uri $resultsUri -Method Get
Write-Host "`n📊 Results:" -ForegroundColor Cyan
Write-Host "Overall Score: $($results.overall_score)" -ForegroundColor Yellow
$results | ConvertTo-Json -Depth 10
```

---

## Error Handling

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| **404** | Video not found | Check `video_id` is correct |
| **404** | Results not found | Wait for status to be "completed" |
| **400** | Invalid sport/exercise_type | Check supported values |
| **413** | File too large | Use video < 100MB |
| **400** | Video too long | Use video < 60 seconds |

### Status: error

If status shows `"status": "error"`, check the `error` field:

- **"No pose data extracted"** → Ensure person is visible in video
- **"Video file not found"** → Internal server issue (contact support)
- **Other errors** → Check video format/quality

---

## Railway Logs Verification

After upload, check Railway logs to verify:

1. **Upload received:**
   ```
   Upload received - sport: basketball, exercise_type: jumpshot, filename: video.mp4
   Video uploaded successfully, video_id: ...
   ```

2. **Background analysis started:**
   ```
   Background analysis started for video_id: ...
   Video file found, initializing pose estimation for ...
   ```

3. **Analysis progress:**
   ```
   Pose data extracted (150 frames), running analysis for ...
   ```

4. **Completion:**
   ```
   Analysis completed successfully for video_id: ..., analysis_id: ...
   ```

5. **Error (if any):**
   ```
   Analysis failed for video_id: ..., error: ...
   ```

---

## Summary

**Workflow:**
1. **POST** `/api/v1/upload` → Get `video_id`
2. **GET** `/api/v1/upload/status/{video_id}` → Poll until `completed`
3. **GET** `/api/v1/upload/results/{video_id}` → Retrieve analysis

**Key Points:**
- Upload returns immediately (background processing)
- Status must be `completed` before retrieving results
- Use PowerShell or Swagger UI (avoid CMD curl for uploads)
- Check Railway logs for detailed processing information

