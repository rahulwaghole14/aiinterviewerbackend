"""
Google Cloud Storage utility for storing and retrieving PDFs
"""
import os
from typing import Optional
from django.conf import settings

try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("⚠️ google-cloud-storage not available. PDFs will be stored locally.")


def get_gcs_client():
    """Get GCS client instance"""
    if not GCS_AVAILABLE:
        return None
    
    try:
        # Try to get credentials from environment or service account
        client = storage.Client()
        return client
    except Exception as e:
        print(f"⚠️ Error creating GCS client: {e}")
        return None


def get_gcs_bucket_name():
    """Get GCS bucket name from settings"""
    return getattr(settings, 'GCS_BUCKET_NAME', None) or os.environ.get('GCS_BUCKET_NAME')


def upload_pdf_to_gcs(pdf_bytes: bytes, file_path: str, content_type: str = 'application/pdf') -> Optional[str]:
    """
    Upload PDF bytes to Google Cloud Storage
    
    Args:
        pdf_bytes: PDF file content as bytes
        file_path: Path within bucket (e.g., 'pdfs/proctoring_report_123.pdf')
        content_type: MIME type (default: 'application/pdf')
    
    Returns:
        GCS public URL if successful, None otherwise
    """
    if not GCS_AVAILABLE:
        print("⚠️ GCS not available, skipping upload")
        return None
    
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        print("⚠️ GCS_BUCKET_NAME not configured, skipping upload")
        return None
    
    try:
        client = get_gcs_client()
        if not client:
            return None
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        # Upload PDF bytes
        blob.upload_from_string(pdf_bytes, content_type=content_type)
        
        # Make blob publicly readable (optional, or use signed URLs)
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        print(f"✅ PDF uploaded to GCS: {public_url}")
        return public_url
        
    except GoogleCloudError as e:
        print(f"❌ GCS upload error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error uploading to GCS: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_gcs_signed_url(file_path: str, expiration_minutes: int = 60) -> Optional[str]:
    """
    Generate a signed URL for private GCS file access
    
    Args:
        file_path: Path within bucket
        expiration_minutes: URL expiration time in minutes
    
    Returns:
        Signed URL if successful, None otherwise
    """
    if not GCS_AVAILABLE:
        return None
    
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        return None
    
    try:
        client = get_gcs_client()
        if not client:
            return None
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        # Generate signed URL
        url = blob.generate_signed_url(
            expiration=expiration_minutes * 60,  # Convert to seconds
            method='GET'
        )
        return url
        
    except Exception as e:
        print(f"❌ Error generating signed URL: {e}")
        return None


def download_pdf_from_gcs(file_path: str) -> Optional[bytes]:
    """
    Download PDF from Google Cloud Storage
    
    Args:
        file_path: Path within bucket
    
    Returns:
        PDF bytes if successful, None otherwise
    """
    if not GCS_AVAILABLE:
        return None
    
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        return None
    
    try:
        client = get_gcs_client()
        if not client:
            return None
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            print(f"⚠️ File not found in GCS: {file_path}")
            return None
        
        pdf_bytes = blob.download_as_bytes()
        print(f"✅ PDF downloaded from GCS: {file_path}")
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ Error downloading from GCS: {e}")
        return None


def delete_pdf_from_gcs(file_path: str) -> bool:
    """
    Delete PDF from Google Cloud Storage
    
    Args:
        file_path: Path within bucket
    
    Returns:
        True if successful, False otherwise
    """
    if not GCS_AVAILABLE:
        return False
    
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        return False
    
    try:
        client = get_gcs_client()
        if not client:
            return False
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        blob.delete()
        print(f"✅ PDF deleted from GCS: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting from GCS: {e}")
        return False


def upload_video_to_gcs(video_file_path: str, gcs_file_path: str, content_type: str = 'video/mp4') -> Optional[str]:
    """
    Upload video file to Google Cloud Storage
    
    Args:
        video_file_path: Local path to video file
        gcs_file_path: Path within bucket (e.g., 'videos/interview_123.mp4')
        content_type: MIME type (default: 'video/mp4')
    
    Returns:
        GCS public URL if successful, None otherwise
    """
    if not GCS_AVAILABLE:
        print("⚠️ GCS not available, skipping video upload")
        return None
    
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        print("⚠️ GCS_BUCKET_NAME not configured, skipping video upload")
        return None
    
    import os
    if not os.path.exists(video_file_path):
        print(f"⚠️ Video file not found: {video_file_path}")
        return None
    
    try:
        client = get_gcs_client()
        if not client:
            return None
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_file_path)
        
        # Upload video file
        blob.upload_from_filename(video_file_path, content_type=content_type)
        
        # Make blob publicly readable
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        print(f"✅ Video uploaded to GCS: {public_url}")
        return public_url
        
    except GoogleCloudError as e:
        print(f"❌ GCS video upload error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error uploading video to GCS: {e}")
        import traceback
        traceback.print_exc()
        return None

