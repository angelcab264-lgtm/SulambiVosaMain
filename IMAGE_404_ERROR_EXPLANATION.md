# Image 404 Error Explanation

## Problem Summary

Your application is experiencing 404 errors when trying to load images from:
```
https://sulambi-backend1.onrender.com/uploads/{filename}
```

Examples of failing requests:
- `3b53b755-9895-4761-a52c-a521a9d7ec7aEVENT%203.webp`
- `05ec61fb-8306-44bc-ba92-9efccecc5262tras.jpg`
- `621db068-ea94-4d0d-9224-ce21114164c8dfsdas.png`
- `0b20239c-4aae-4f9c-b5fc-4b2c4d2a9d71bf.jpg`

## Root Cause

**⚠️ CRITICAL ISSUE: Render's Ephemeral Filesystem**

The 404 errors are occurring because **the uploaded image files no longer exist on the server**. This is due to Render's filesystem being **ephemeral** (temporary):

1. **Files are lost on restart**: When your Render service restarts (which happens automatically during deployments, updates, or after periods of inactivity), all files in the `uploads/` directory are deleted.

2. **Free tier spin-down**: On Render's free tier, services automatically spin down after 15 minutes of inactivity. When they spin down, the filesystem is cleared, and all uploaded files are lost.

3. **Database vs Filesystem mismatch**: Your database still contains references to these image files (the filenames/paths), but the actual files have been deleted from the server's filesystem.

## Current Architecture

### Backend (Flask)
- **File Upload**: Files are saved to `uploads/` directory via `app/utils/multipartFileWriter.py`
- **File Serving**: Files are served via route `/uploads/<path:path>` in `server.py` (lines 49-56)
- **Storage**: Local filesystem only (not persistent on Render)

### Frontend
- **URL Construction**: Correctly constructs URLs like `${BASE_URL}/uploads/${filename}?t=${timestamp}`
- **BASE_URL**: Derived from `VITE_API_URI` environment variable (with `/api` suffix removed)

## Why This Happens

1. User uploads an image → File saved to `uploads/` directory → Database stores filename
2. Service restarts or spins down → Filesystem is cleared → Files are deleted
3. Frontend tries to load image → 404 error because file doesn't exist

## Solutions

### Option 1: Use Cloud Storage (Recommended for Production)

**Best long-term solution** - Store files in cloud storage that persists independently of your server.

#### Using AWS S3 (Example)

1. **Install boto3**:
   ```bash
   pip install boto3
   ```

2. **Update `app/utils/multipartFileWriter.py`**:
   ```python
   import boto3
   from uuid import uuid4
   import os
   from flask import request
   
   s3_client = boto3.client('s3')
   S3_BUCKET = os.getenv('S3_BUCKET_NAME')
   
   def basicFileWriter(keys: list[str]):
       keyPaths = {}
       filenames = list(request.files)
       
       for k in filenames:
           file = request.files.get(k)
           if file is None or file.filename == "":
               continue
           
           # Generate unique filename
           filename = str(uuid4()) + file.filename
           
           # Upload to S3
           s3_client.upload_fileobj(
               file,
               S3_BUCKET,
               f"uploads/{filename}",
               ExtraArgs={'ContentType': file.content_type}
           )
           
           # Store S3 URL or path
           keyPaths[k] = f"uploads/{filename}"
       
       return keyPaths
   ```

3. **Update `server.py` to serve from S3**:
   ```python
   @Server.route("/uploads/<path:path>")
   def staticFileHost(path):
       # Generate presigned URL for S3 file
       url = s3_client.generate_presigned_url(
           'get_object',
           Params={'Bucket': S3_BUCKET, 'Key': f"uploads/{path}"},
           ExpiresIn=3600
       )
       return redirect(url)
   ```

4. **Set environment variables in Render**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET_NAME`
   - `AWS_REGION`

#### Using Cloudinary (Easier for Images)

1. **Install cloudinary**:
   ```bash
   pip install cloudinary
   ```

2. **Update file writer**:
   ```python
   import cloudinary
   import cloudinary.uploader
   from uuid import uuid4
   from flask import request
   
   cloudinary.config(
       cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
       api_key=os.getenv('CLOUDINARY_API_KEY'),
       api_secret=os.getenv('CLOUDINARY_API_SECRET')
   )
   
   def basicFileWriter(keys: list[str]):
       keyPaths = {}
       filenames = list(request.files)
       
       for k in filenames:
           file = request.files.get(k)
           if file is None or file.filename == "":
               continue
           
           # Upload to Cloudinary
           result = cloudinary.uploader.upload(
               file,
               folder="uploads",
               public_id=str(uuid4())
           )
           
           # Store Cloudinary URL
           keyPaths[k] = result['secure_url']
       
       return keyPaths
   ```

3. **Update frontend** to use Cloudinary URLs directly (no backend route needed)

### Option 2: Use Render Disk (Paid Feature)

If you upgrade to a paid Render plan, you can use Render Disk for persistent storage:

1. Add a Render Disk to your service
2. Mount it to a persistent path
3. Update `BASIC_WRITER_PATH` in `multipartFileWriter.py` to use the mounted disk path

### Option 3: Temporary Workaround (Not Recommended for Production)

For development/testing only, you can:

1. **Re-upload missing images** manually
2. **Keep service active** (prevent spin-down by using a paid plan or keep-alive pings)
3. **Accept data loss** on restarts (not suitable for production)

## Immediate Actions

1. **Verify the issue**: Check if files exist in the `uploads/` directory on your Render service
2. **Check service logs**: Look for file upload errors or filesystem issues
3. **Choose a solution**: Implement cloud storage (Option 1) for production use
4. **Update database**: Consider cleaning up references to non-existent files

## Testing the Fix

After implementing cloud storage:

1. Upload a new image
2. Verify it's stored in cloud storage
3. Check that the frontend can load it
4. Restart your Render service
5. Verify the image still loads (should work since it's in cloud storage)

## Additional Notes

- Your current code structure is correct - the issue is purely infrastructure-related
- The frontend URL construction is working properly
- The backend route for serving files is correctly configured
- The only missing piece is persistent file storage

## References

- Render Documentation: https://render.com/docs
- AWS S3 Python SDK: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- Cloudinary Python SDK: https://cloudinary.com/documentation/python_integration






