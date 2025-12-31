# Railway Deployment - OpenCV Headless Fix

## ✅ Changes Committed

**Commit:** `824add2` - "fix: force headless OpenCV to resolve Railway libGL crash"

### Files Changed:
1. `requirements.txt` - Only `opencv-contrib-python-headless==4.11.0.86` (single OpenCV package)
2. `app/core/pose_estimator.py` - Added Linux safety check to prevent GUI OpenCV deployment

### Verification:
- ✅ Only ONE OpenCV dependency in requirements.txt
- ✅ No GUI OpenCV functions used in codebase
- ✅ Safety check added (prevents non-headless OpenCV on Linux)
- ✅ MediaPipe compatibility verified

---

## 🚀 Deployment Steps

### Step 1: Push to Git

```bash
git push
```

Railway will auto-detect the push and attempt to deploy, but you need to clear the cache.

### Step 2: Clear Build Cache & Redeploy (CRITICAL)

**⚠️ IMPORTANT: Do NOT just click "Restart" - you MUST clear the build cache!**

1. Go to **Railway Dashboard** → Your Backend Service
2. Click **⋮** (three dots menu) → **Redeploy**
3. **Enable "Clear build cache"** ✅
4. Click **Deploy**

This ensures Railway rebuilds with the new `opencv-contrib-python-headless` package instead of using cached GUI OpenCV.

### Step 3: Verify Deployment

After deployment completes:

1. Check **Logs** tab - should see:
   - ✅ `Successfully installed opencv-contrib-python-headless`
   - ✅ No `libGL.so.1` errors
   - ✅ FastAPI starts successfully

2. Test health endpoint:
   ```bash
   curl https://your-app.railway.app/health
   ```
   Expected: `{"status":"healthy"}`

3. Test pose estimation (upload endpoint should work)

---

## 🎯 Expected Results

✅ **Build succeeds** - No ImportError during OpenCV import  
✅ **Server starts** - FastAPI runs without crashes  
✅ **No libGL.so.1 errors** - Headless OpenCV doesn't require GUI libraries  
✅ **Pose estimation works** - Video upload and processing functional  

---

## 🔍 Troubleshooting

### If build still fails:

1. **Verify requirements.txt** - Should have exactly one `opencv-contrib-python-headless` line
2. **Check Railway logs** - Look for which OpenCV package is being installed
3. **Force clean build** - Delete and recreate the Railway service if cache persists

### If ImportError persists:

Check Railway logs for:
- `opencv-python` being installed (wrong package)
- `opencv-contrib-python` being installed (wrong package)
- Multiple OpenCV packages conflicting

Solution: Ensure `requirements.txt` has ONLY `opencv-contrib-python-headless==4.11.0.86`

---

## ✅ Final Checklist

- [ ] `requirements.txt` has exactly one OpenCV package (headless)
- [ ] Code committed and pushed
- [ ] Railway cache cleared during redeploy
- [ ] Build succeeds without ImportError
- [ ] `/health` endpoint returns 200 OK
- [ ] Upload endpoint accepts video files

**Status:** ✅ Ready for Railway deployment





