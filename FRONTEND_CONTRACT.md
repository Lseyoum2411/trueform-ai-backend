# Frontend-Backend API Contract

This document defines the exact API contract between the frontend and backend. Use this to build the UI without reading backend code.

**Base URL:** `https://trueform-ai-backend-production.up.railway.app`

**API Prefix:** `/api/v1`

---

## Authentication

Currently: **None** (public API)

Future: May require authentication headers.

---

## Endpoints

### 1. Health Check

**GET** `/`

**Response:**
```json
{
  "status": "ok"
}
```

**Purpose:** Verify backend is online.

---

### 2. Health Endpoint

**GET** `/health`

**Response:**
```json
{
  "status": "ok"
}
```

---

### 3. Get Sports

**GET** `/api/v1/sports`

**Response:**
```json
[
  {
    "id": "basketball",
    "name": "Basketball",
    "description": "Analyze jump shot form",
    "requires_exercise_type": false,
    "exercise_types": [
      {
        "id": "jumpshot",
        "name": "Jump Shot",
        "description": "Standard jump shot form analysis"
      }
    ],
    "lift_types": null
  },
  {
    "id": "golf",
    "name": "Golf",
    "description": "Analyze golf swing mechanics",
    "requires_exercise_type": true,
    "exercise_types": [
      {
        "id": "driver",
        "name": "Driver",
        "description": "Full power drive from tee"
      },
      {
        "id": "iron",
        "name": "Iron",
        "description": "Iron shot analysis"
      }
    ],
    "lift_types": null
  },
  {
    "id": "weightlifting",
    "name": "Weightlifting",
    "description": "Analyze form for different lifts",
    "requires_exercise_type": true,
    "exercise_types": [
      {
        "id": "back_squat",
        "name": "Back Squat",
        "description": "Barbell on upper back, full depth squat"
      }
      // ... more exercise types
    ],
    "lift_types": null
  }
]
```

**Purpose:** Get list of supported sports and their exercise types.

---

### 4. Upload Video

**POST** `/api/v1/upload`

**Content-Type:** `multipart/form-data`

**Required Fields:**
- `video` (file): Video file (< 100MB, < 60 seconds)
- `sport` (string): One of `"basketball"`, `"golf"`, `"weightlifting"`
- `exercise_type` (string, optional): 
  - Required for `golf` and `weightlifting`
  - Auto-set to `"jumpshot"` for `basketball`
  - See `/api/v1/sports` for valid values

**Success Response (200):**
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
  "status": "queued",
  "next_poll_url": "/api/v1/upload/status/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

| Status | Error | Cause |
|--------|-------|-------|
| 400 | `Unsupported sport: {sport}` | Invalid sport value |
| 400 | `exercise_type required for {sport}` | Missing required exercise_type |
| 400 | `Unsupported exercise_type '{type}' for sport '{sport}'` | Invalid exercise_type |
| 413 | `File size exceeds 100MB limit` | File too large |
| 400 | `Video duration exceeds 60 seconds` | Video too long |
| 429 | `Analysis queue is full. Please try again later.` | Too many concurrent analyses |

**Purpose:** Upload video and queue for analysis. Returns immediately with `video_id` and `next_poll_url`.

**Frontend Behavior:**
1. Upload file using multipart form
2. Extract `video_id` from response
3. Poll `next_poll_url` (or `/api/v1/upload/status/{video_id}`) until status is `completed` or `error`

---

### 5. Get Video Status

**GET** `/api/v1/upload/status/{video_id}`

**Path Parameters:**
- `video_id` (string, required): Video ID from upload response

**Success Response (200):**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 60.0,
  "analysis_id": null,
  "error": null,
  "created_at": "2025-12-23T12:00:00",
  "updated_at": "2025-12-23T12:00:05"
}
```

**Status Values:**
- `"queued"` - Waiting to start analysis
- `"processing"` - Analysis in progress
- `"completed"` - Analysis finished successfully
- `"error"` - Analysis failed

**Progress:** `0.0` to `100.0` (nullable if not available)

**Error Response (404):**
```json
{
  "detail": "Video not found"
}
```

**Purpose:** Check processing status. Poll this endpoint until `status` is `"completed"` or `"error"`.

**Frontend Behavior:**
1. Poll every 2-3 seconds
2. Display progress bar if `progress` is not null
3. Stop polling when `status` is `"completed"` or `"error"`
4. If `status` is `"error"`, display `error` message to user
5. If `status` is `"completed"`, proceed to fetch results

---

### 6. Get Analysis Results

**GET** `/api/v1/upload/results/{video_id}`

**Path Parameters:**
- `video_id` (string, required): Video ID from upload response

**Success Response (200):**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_id": "abc123-def456-ghi789",
  "sport": "basketball",
  "exercise_type": "jumpshot",
  "lift_type": null,
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
      "severity": "info",
      "timestamp": null
    }
  ],
  "strengths": ["Excellent follow-through", "Good balance"],
  "weaknesses": ["Slight forward lean"],
  "areas_for_improvement": ["Slight forward lean", "Timing could improve"],
  "frames_analyzed": 150,
  "processing_time": 12.5,
  "analyzed_at": "2025-12-23T12:05:30"
}
```

**Error Response (404):**
```json
{
  "detail": "Analysis results not found"
}
```

**Purpose:** Retrieve completed analysis results. Only available when status is `"completed"`.

**Frontend Behavior:**
1. Only call this endpoint after status is `"completed"`
2. Display `overall_score`, `scores`, `feedback`, `strengths`, `weaknesses`
3. Handle 404 gracefully (show "Results not ready" message)

---

## Error Handling

### Standard Error Format

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|----------------|
| 200 | Success | Process response |
| 400 | Bad Request | Show error message to user |
| 404 | Not Found | Show "not found" message |
| 413 | Payload Too Large | Show file size limit message |
| 429 | Too Many Requests | Show "queue full, try later" message |
| 422 | Validation Error | Show validation error details |
| 500 | Server Error | Show generic error, suggest retry |

### Error Cases

**Upload Errors:**
- Invalid sport → 400
- Missing/invalid exercise_type → 400
- File too large → 413
- Video too long → 400
- Queue full → 429

**Status Errors:**
- Video not found → 404

**Results Errors:**
- Results not found → 404 (usually means still processing)

---

## Frontend Workflow

### Complete Upload → Results Flow

1. **Get Sports List**
   ```
   GET /api/v1/sports
   ```
   - Display sports to user
   - Show exercise type selector if `requires_exercise_type: true`

2. **Upload Video**
   ```
   POST /api/v1/upload
   FormData: { video: File, sport: string, exercise_type?: string }
   ```
   - Show upload progress (if supported)
   - Extract `video_id` from response
   - Store `next_poll_url` or construct from `video_id`

3. **Poll Status**
   ```
   GET /api/v1/upload/status/{video_id}
   ```
   - Poll every 2-3 seconds
   - Display progress bar (if `progress` is not null)
   - Show status message to user
   - Stop when `status` is `"completed"` or `"error"`

4. **Handle Completion**
   - If `status: "completed"` → Fetch results
   - If `status: "error"` → Display error message, allow retry

5. **Get Results**
   ```
   GET /api/v1/upload/results/{video_id}
   ```
   - Display analysis results
   - Show overall score, metrics, feedback
   - Highlight strengths and areas for improvement

---

## Request Examples

### JavaScript (Fetch API)

```javascript
// Upload video
const formData = new FormData();
formData.append('video', fileInput.files[0]);
formData.append('sport', 'basketball');

const uploadResponse = await fetch('https://trueform-ai-backend-production.up.railway.app/api/v1/upload', {
  method: 'POST',
  body: formData
});

const uploadData = await uploadResponse.json();
const videoId = uploadData.video_id;

// Poll status
const pollStatus = async () => {
  const statusResponse = await fetch(
    `https://trueform-ai-backend-production.up.railway.app/api/v1/upload/status/${videoId}`
  );
  return await statusResponse.json();
};

// Get results
const resultsResponse = await fetch(
  `https://trueform-ai-backend-production.up.railway.app/api/v1/upload/results/${videoId}`
);
const results = await resultsResponse.json();
```

### TypeScript Types

```typescript
interface VideoUploadResponse {
  video_id: string;
  filename: string;
  sport: string;
  exercise_type: string | null;
  lift_type: string | null;
  uploaded_at: string;
  file_size: number;
  duration: number | null;
  status: "queued";
  next_poll_url: string;
}

interface VideoStatusResponse {
  video_id: string;
  status: "queued" | "processing" | "completed" | "error";
  progress: number | null;
  analysis_id: string | null;
  error: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface AnalysisResult {
  video_id: string;
  analysis_id: string;
  sport: string;
  exercise_type: string | null;
  overall_score: number;
  scores: Record<string, number>;
  feedback: Array<{
    category: string;
    aspect: string;
    message: string;
    severity: string;
    timestamp: number | null;
  }>;
  strengths: string[];
  weaknesses: string[];
  areas_for_improvement: string[];
  frames_analyzed: number;
  processing_time: number;
  analyzed_at: string;
}
```

---

## Rate Limiting

**Limit:** Maximum 3 concurrent analyses

**Behavior:**
- If limit exceeded, upload returns 429 error
- Frontend should:
  - Show "Queue full, please try again later"
  - Allow user to retry after delay
  - Optionally show wait time estimate

---

## File Requirements

- **Max Size:** 100 MB
- **Max Duration:** 60 seconds
- **Formats:** MP4, MOV, AVI (any format supported by OpenCV)
- **Content:** Must contain visible person for pose detection

---

## Notes for Frontend Developers

1. **Field Name:** Upload field MUST be named `"video"` (not `"file"`)

2. **Polling Strategy:**
   - Start polling immediately after upload
   - Poll every 2-3 seconds
   - Stop when status is terminal (`completed` or `error`)
   - Add exponential backoff if needed

3. **Error Handling:**
   - Always check response status codes
   - Display user-friendly error messages
   - Allow retry for transient errors (429, 500)

4. **Progress Display:**
   - Show progress bar if `progress` is not null
   - Update status text based on `status` value
   - Show estimated time remaining (optional)

5. **Results Display:**
   - Only fetch results when status is `"completed"`
   - Handle 404 gracefully (results not ready)
   - Display scores, feedback, and improvement areas clearly

---

## Swagger Documentation

Interactive API documentation available at:
`https://trueform-ai-backend-production.up.railway.app/docs`

Use this to test endpoints and see exact request/response formats.


<<<<<<< HEAD


=======
>>>>>>> 3cec07eb73eb7a9d41527c45e27aa974b9b882ec
