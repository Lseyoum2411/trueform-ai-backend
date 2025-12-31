# FastAPI Upload 422 Error Analysis & Fix

## Root Cause Identified

### Server-Side Function Signature

```python
@router.post("", response_model=VideoUpload)
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),  # ← Parameter name is "video"
    sport: str = Form(...),
    exercise_type: Optional[str] = Form(None),
):
```

### The Problem

**FastAPI requires the multipart form field name to EXACTLY match the function parameter name.**

- Server expects: `video` (matches parameter `video: UploadFile`)
- Client sends: `file` (mismatch!)

When the field name doesn't match, FastAPI's request validation (Pydantic v2) rejects it with:
```json
{
  "detail": [{
    "type": "missing",
    "loc": ["body", "video"],
    "msg": "Field required"
  }]
}
```

---

## Why FastAPI Behaves This Way

### FastAPI Request Validation Flow

1. **Request arrives** → FastAPI parses multipart/form-data
2. **Field extraction** → FastAPI looks for form fields matching parameter names
3. **Parameter binding** → Fields are bound to function parameters by name
4. **Validation** → Pydantic validates required fields
5. **Error if missing** → If a required field (marked with `...`) is missing → 422

### Why `File(...)` Shows as "Field required"

- `File(...)` means "required field"
- FastAPI looks for form field named `video` (the parameter name)
- Finds `file` instead → doesn't match → treats as missing → 422 error

---

## Correct curl Command (Windows CMD)

### Fixed Command

```cmd
curl -X POST "https://trueform-ai-backend-production.up.railway.app/api/v1/upload" ^
  -F "video=@C:\Users\lksey\Downloads\1560A327-8004-45A6-8BB0-486444FDDFD3.mp4" ^
  -F "sport=golf" ^
  -F "exercise_type=driver"
```

**Key change:** `-F "file=@..."` → `-F "video=@..."`

### Alternative (Single Line)

```cmd
curl -X POST "https://trueform-ai-backend-production.up.railway.app/api/v1/upload" -F "video=@C:\Users\lksey\Downloads\1560A327-8004-45A6-8BB0-486444FDDFD3.mp4" -F "sport=golf" -F "exercise_type=driver"
```

---

## PowerShell Command (Recommended)

```powershell
$uri = "https://trueform-ai-backend-production.up.railway.app/api/v1/upload"
$filePath = "C:\Users\lksey\Downloads\1560A327-8004-45A6-8BB0-486444FDDFD3.mp4"

$form = @{
    video = Get-Item -Path $filePath  # ← Must match parameter name "video"
    sport = "golf"
    exercise_type = "driver"
}

$response = Invoke-WebRequest -Uri $uri -Method Post -Form $form
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## Why Earlier Attempts Showed "ERROR"

### Generic "ERROR" Response

When you saw just `ERROR` without details, it was likely due to:

1. **CMD line continuation issues** - The `^` character in CMD can cause parsing problems
2. **Incomplete request** - Shell may not have properly sent all form fields
3. **Connection errors** - Network issues before validation could occur
4. **Missing verbose flag** - Without `-v`, curl hides detailed error messages

### Why Verbose (`-v`) Helped

- Shows HTTP status code (422)
- Shows response body with Pydantic error details
- Confirms the request reached the server
- Reveals what FastAPI actually received

---

## Windows Shell Behavior Differences

### CMD (cmd.exe)

```cmd
# Line continuation with ^
curl -X POST "url" ^
  -F "video=@file.mp4"

# Issues:
# - ^ must be last character on line (no trailing spaces)
# - Paths with spaces need quotes
# - Some characters may need escaping
```

### PowerShell (powershell.exe)

```powershell
# Better for complex requests
$form = @{
    video = Get-Item -Path $filePath
    sport = "golf"
}
Invoke-WebRequest -Uri $uri -Method Post -Form $form

# Advantages:
# - Native multipart form support
# - Better error handling
# - Easier to read and debug
```

### Git Bash / WSL

```bash
# Unix-style syntax
curl -X POST "url" \
  -F "video=@file.mp4" \
  -F "sport=golf"

# Works like Linux curl
```

---

## Expected Success Response

After fixing the field name, you should receive:

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000.mp4",
  "sport": "golf",
  "exercise_type": "driver",
  "lift_type": null,
  "uploaded_at": "2025-12-23T06:45:00",
  "file_size": 2921659,
  "duration": 12.5,
  "status": "queued"
}
```

---

## Prevention Checklist

### ✅ Always Verify Field Names Match Parameter Names

1. **Check the function signature:**
   ```python
   async def upload_video(
       video: UploadFile = File(...),  # ← Field name must be "video"
   ```
2. **Match form field to parameter:**
   ```bash
   -F "video=@file.mp4"  # ← Must match "video" parameter
   ```

### ✅ Use Appropriate Tools for Your Shell

- **CMD**: Use `curl` with proper escaping
- **PowerShell**: Use `Invoke-WebRequest -Form` (preferred)
- **Bash/WSL**: Use `curl` with standard syntax

### ✅ Always Use Verbose Mode for Debugging

```cmd
curl -v -X POST "url" ...  # Shows full request/response
```

### ✅ Test with Swagger UI First

1. Go to `https://your-domain/docs`
2. Try the endpoint in the interactive docs
3. Check the request payload format
4. Copy the exact field names

### ✅ Read FastAPI Error Messages Carefully

- `422 Unprocessable Entity` = Validation error
- `"Field required"` = Missing or incorrectly named field
- `"loc": ["body", "video"]` = Tells you exactly which field is wrong

### ✅ Document Field Names in API Docs

If you change parameter names, update:
- OpenAPI/Swagger docs
- Client examples
- Test scripts

---

## Quick Reference: FastAPI Multipart Form Rules

1. **Field name = Parameter name** (case-sensitive)
2. **Required fields** use `File(...)` or `Form(...)` with `...`
3. **Optional fields** use `File(None)` or `Form(None)`
4. **File uploads** use `UploadFile = File(...)`
5. **Form data** uses `str = Form(...)` or `Optional[str] = Form(None)`

---

## Summary

**Problem:** Client sent `file` but server expects `video`

**Solution:** Change form field name to match parameter name: `video`

**Root Cause:** FastAPI/Pydantic requires exact field name matching for multipart form validation

**Fix:** `-F "video=@file.mp4"` instead of `-F "file=@file.mp4"`




