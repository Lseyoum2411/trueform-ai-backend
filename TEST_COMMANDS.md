# Test Commands for TrueForm AI Backend

## Step 1: Setup & Health Check

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"healthy"}
```

## Step 2: Get Sports List

```bash
curl http://localhost:8000/api/v1/sports

# Expected: JSON array with 3 sports + exercise types
```

## Step 3: Upload Video

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "video=@test.mp4" \
  -F "sport=basketball" \
  -F "exercise_type=jumpshot"

# Expected: {"video_id":"...", "status":"queued", ...}
# Save the video_id from response
```

## Step 4: Check Status

```bash
# Replace {video_id} with actual ID from upload response
curl http://localhost:8000/api/v1/status/{video_id}

# Expected: {"video_id":"...", "status":"processing"|"completed", "progress":...}
```

## Step 5: Get Results

```bash
# Replace {video_id} with actual ID
curl http://localhost:8000/api/v1/status/results/{video_id}

# Expected: Full analysis result with metrics, feedback, scores
```

## Test Pose Estimation Directly

```bash
cd backend
python test_pose.py test.mp4

# Expected: Prints pose data and saves to pose_test_output.json
```





