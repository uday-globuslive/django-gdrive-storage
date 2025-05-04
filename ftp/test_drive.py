import os
import sys
import logging
import tempfile
from django.conf import settings
from gdrive import GoogleDriveService

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_google_drive_upload():
    """Test Google Drive API connectivity by creating a test file and uploading it."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp:
        temp.write(b"This is a test file for Google Drive API connectivity test.")
        temp_path = temp.name
    
    try:
        logger.info("Initializing Google Drive service...")
        drive_service = GoogleDriveService()
        
        if not drive_service.service:
            logger.error("Failed to initialize Google Drive service.")
            return
        
        # Create a test folder
        logger.info("Creating test folder...")
        folder_name = "gdriveftp_test_folder"
        folder_id = drive_service.create_user_folder(folder_name)
        
        if not folder_id:
            logger.error("Failed to create test folder.")
            return
        
        # Upload the test file
        logger.info(f"Uploading test file from {temp_path}...")
        file_id = drive_service.upload_file(
            temp_path,
            "test_file.txt",
            folder_id
        )
        
        if not file_id:
            logger.error("Failed to upload test file.")
            return
        
        logger.info(f"Test file uploaded successfully with ID: {file_id}")
        logger.info("Google Drive API is working correctly!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    # Initialize Django settings
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gdriveftp.settings')
    django.setup()
    
    # Run the test
    test_google_drive_upload()