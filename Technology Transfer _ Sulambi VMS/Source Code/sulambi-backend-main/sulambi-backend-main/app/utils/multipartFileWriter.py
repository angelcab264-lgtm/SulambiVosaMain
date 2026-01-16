from flask import request
from uuid import uuid4
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from werkzeug.exceptions import BadRequest

load_dotenv()

BASIC_WRITER_PATH = "uploads"

# Allowed file extensions for requirements documents
ALLOWED_EXTENSIONS = {
    'pdf',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif'
}

# MIME types for validation
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
    'image/bmp', 'image/webp', 'image/svg+xml', 'image/x-icon',
    'image/tiff', 'image/x-tiff'
}

def is_allowed_file(filename: str, content_type: str) -> bool:
    """
    Check if file is allowed based on extension and MIME type.
    Only PDF and image files are allowed.
    """
    if not filename:
        return False
    
    # Check file extension
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check MIME type
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        return False
    
    return True

def cloudinaryFileWriter(keys: list[str], folder: str = "requirements"):
    """
    Upload files to Cloudinary with validation.
    Only allows PDF and image file formats.
    
    REQUIRES Cloudinary configuration - will NOT fall back to local storage.
    All files MUST be uploaded to Cloudinary.
    
    Args:
        keys: List of file field names to process
        folder: Cloudinary folder to store files in (default: "requirements")
    
    Returns:
        dict: Dictionary mapping file keys to Cloudinary URLs
    
    Raises:
        BadRequest: If Cloudinary is not configured, file type is not allowed, or upload fails
    """
    keyPaths = {}
    filenames = list(request.files)
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    
    # STRICT: Check if Cloudinary is configured - NO FALLBACK TO LOCAL STORAGE
    cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if not all([cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret]):
        error_msg = (
            "Cloudinary configuration is missing. "
            "All file uploads must use Cloudinary. "
            "Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET environment variables. "
            "Local file storage is disabled for security and scalability."
        )
        print(f"[CLOUDINARY_UPLOAD] ❌ ERROR: {error_msg}")
        raise BadRequest(error_msg)
    
    print(f"[CLOUDINARY_UPLOAD] ✅ Cloudinary configured. Cloud: {cloudinary_cloud_name}")
    
    for k in filenames:
        if k not in keys:
            continue
            
        file = request.files.get(k)
        if file is None:
            continue
        if file.filename == "":
            continue
        
        # Validate file type
        if not is_allowed_file(file.filename, file.content_type):
            raise BadRequest(
                f"File '{file.filename}' is not allowed. "
                f"Only PDF and image files (jpg, jpeg, png, gif, bmp, webp, svg, ico, tiff) are allowed."
            )
        
        try:
            # Generate unique filename
            unique_filename = f"{str(uuid4())}_{file.filename}"
            
            print(f"[CLOUDINARY_UPLOAD] Uploading {k}: {file.filename} to Cloudinary folder '{folder}'...")
            
            # Upload to Cloudinary - NO FALLBACK TO LOCAL STORAGE
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                public_id=unique_filename.rsplit('.', 1)[0],  # Remove extension for public_id
                resource_type="auto",  # Auto-detect resource type (image, pdf, etc.)
                overwrite=False,
                use_filename=False,
                unique_filename=True
            )
            
            # Store the secure URL (or regular URL if secure is not available)
            cloudinary_url = result.get('secure_url') or result.get('url')
            
            if not cloudinary_url:
                raise Exception("Cloudinary upload succeeded but no URL was returned")
            
            # Verify it's a Cloudinary URL (not a local path)
            if not cloudinary_url.startswith('http://') and not cloudinary_url.startswith('https://'):
                raise Exception(f"Invalid Cloudinary URL format: {cloudinary_url}")
            
            keyPaths[k] = cloudinary_url
            
            print(f"[CLOUDINARY_UPLOAD] ✅ Successfully uploaded {k}: {file.filename}")
            print(f"[CLOUDINARY_UPLOAD]    URL: {cloudinary_url[:80]}...")
            
        except Exception as e:
            error_msg = f"Failed to upload file '{file.filename}' to Cloudinary: {str(e)}"
            print(f"[CLOUDINARY_UPLOAD] ❌ ERROR: {error_msg}")
            print(f"[CLOUDINARY_UPLOAD] ❌ Local storage fallback is disabled. Upload must succeed in Cloudinary.")
            raise BadRequest(error_msg)
    
    return keyPaths

def basicFileWriter(keys: list[str]):
    """
    Legacy function for local file storage.
    Kept for backward compatibility, but consider using cloudinaryFileWriter for production.
    """
    keyPaths = {}
    filenames = list(request.files)

    for k in filenames:
        file = request.files.get(k)
        if (file == None): continue
        if (file.filename == ""): continue

        # generate unique filenames to prevent overwrites
        fwpath = os.path.join(BASIC_WRITER_PATH, str(uuid4()) + file.filename)
        file.save(fwpath)
        keyPaths[k] = fwpath

    return keyPaths