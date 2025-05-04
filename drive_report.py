#!/usr/bin/env python
"""
Google Drive API Test Report Generator

This script performs a series of tests to diagnose Google Drive API integration issues
and generates a comprehensive report.
"""

import os
import sys
import json
import logging
import tempfile
import platform
import datetime
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('drive_report.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_system_info():
    """Generate system information for the report."""
    info = {
        "Platform": platform.platform(),
        "Python Version": platform.python_version(),
        "Timestamp": datetime.datetime.now().isoformat(),
    }
    
    logger.info("System Information:")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")
    
    return info

def check_credentials_file():
    """Check if credentials.json exists and is valid."""
    logger.info("Checking credentials file...")
    
    credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    
    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found at: {credentials_path}")
        return {"status": "error", "message": "Credentials file not found"}
    
    try:
        with open(credentials_path, 'r') as f:
            cred_data = json.load(f)
            
        required_keys = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_keys = [key for key in required_keys if key not in cred_data]
        
        if missing_keys:
            logger.error(f"Credentials file is missing required keys: {', '.join(missing_keys)}")
            return {"status": "error", "message": f"Credentials file is missing required keys: {', '.join(missing_keys)}"}
        
        logger.info(f"Credentials file is valid. Service account: {cred_data.get('client_email')}")
        return {
            "status": "success", 
            "message": "Credentials file is valid",
            "service_account": cred_data.get('client_email'),
            "project_id": cred_data.get('project_id')
        }
        
    except json.JSONDecodeError:
        logger.error("Credentials file is not valid JSON")
        return {"status": "error", "message": "Credentials file is not valid JSON"}
    except Exception as e:
        logger.error(f"Error checking credentials file: {str(e)}")
        return {"status": "error", "message": f"Error checking credentials file: {str(e)}"}

def test_drive_api(share_email=None):
    """Test Google Drive API connectivity."""
    logger.info("Testing Google Drive API connectivity...")
    
    # Initialize Django
    try:
        logger.info("Initializing Django...")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gdriveftp.settings')
        import django
        django.setup()
        
        from ftp.gdrive import GoogleDriveService
        
    except Exception as e:
        logger.error(f"Failed to initialize Django: {str(e)}")
        return {"status": "error", "message": f"Failed to initialize Django: {str(e)}"}
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp:
        test_content = f"Google Drive API Test - {datetime.datetime.now().isoformat()}"
        temp.write(test_content.encode('utf-8'))
        temp_path = temp.name
    
    try:
        # Initialize Drive service
        drive_service = GoogleDriveService()
        
        if not drive_service.service:
            logger.error("Failed to initialize Google Drive service")
            return {"status": "error", "message": "Failed to initialize Google Drive service"}
        
        # Test folder creation
        folder_name = f"gdriveftp_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating test folder: {folder_name}")
        
        folder_id = drive_service.create_user_folder(folder_name, share_with_email=share_email)
        
        if not folder_id:
            logger.error("Failed to create test folder")
            return {"status": "error", "message": "Failed to create test folder"}
        
        logger.info(f"Test folder created with ID: {folder_id}")
        
        # Test file upload
        file_name = f"test_file_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logger.info(f"Uploading test file: {file_name}")
        
        file_id = drive_service.upload_file(
            temp_path,
            file_name,
            folder_id,
            share_with_email=share_email
        )
        
        if not file_id:
            logger.error("Failed to upload test file")
            return {
                "status": "error", 
                "message": "Failed to upload test file", 
                "folder_created": True,
                "folder_id": folder_id
            }
        
        logger.info(f"Test file uploaded with ID: {file_id}")
        
        # Get and verify the file metadata
        try:
            file_info = drive_service.service.files().get(
                fileId=file_id, 
                fields="id,name,mimeType,webViewLink,webContentLink"
            ).execute()
            
            logger.info(f"File verification successful: {json.dumps(file_info, indent=2)}")
            
            return {
                "status": "success",
                "message": "Google Drive API tests completed successfully",
                "folder_id": folder_id,
                "folder_name": folder_name,
                "file_id": file_id,
                "file_name": file_name,
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"Error verifying file: {str(e)}")
            return {
                "status": "partial",
                "message": f"File uploaded but verification failed: {str(e)}",
                "folder_id": folder_id,
                "file_id": file_id
            }
            
    except Exception as e:
        logger.error(f"Drive API test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": f"Drive API test failed: {str(e)}"}
    
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def generate_report(share_email=None):
    """Generate a complete report on Google Drive API integration."""
    logger.info("=" * 60)
    logger.info("GOOGLE DRIVE API INTEGRATION REPORT")
    logger.info("=" * 60)
    
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system_info": generate_system_info(),
        "credentials_check": check_credentials_file(),
    }
    
    if report["credentials_check"]["status"] == "success":
        report["drive_api_test"] = test_drive_api(share_email)
    else:
        report["drive_api_test"] = {
            "status": "skipped", 
            "message": "Skipped due to credentials issue"
        }
    
    # Generate summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    
    if report["credentials_check"]["status"] == "success" and report["drive_api_test"]["status"] == "success":
        logger.info("✅ Google Drive API Integration is WORKING CORRECTLY")
        
        # Add viewing instructions
        if "file_info" in report["drive_api_test"]:
            webViewLink = report["drive_api_test"]["file_info"].get("webViewLink")
            if webViewLink:
                logger.info(f"\nYou can view your test file here: {webViewLink}")
                
            logger.info("\nIf you've provided a sharing email, also check your 'Shared with me' section in Google Drive.")
            
    elif report["credentials_check"]["status"] != "success":
        logger.info("❌ Google Drive API Integration is NOT WORKING")
        logger.info(f"   Reason: Credentials issue - {report['credentials_check']['message']}")
    elif report["drive_api_test"]["status"] != "success":
        logger.info("❌ Google Drive API Integration is NOT WORKING")
        logger.info(f"   Reason: API test failed - {report['drive_api_test']['message']}")
    
    # Write report to file
    report_file = "drive_api_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nDetailed report saved to: {report_file}")
    logger.info(f"Log file saved to: drive_report.log")
    
    return report

if __name__ == "__main__":
    # Check if email was provided
    share_email = None
    if len(sys.argv) > 1:
        share_email = sys.argv[1]
        logger.info(f"Will share test files with: {share_email}")
    
    # Generate report
    generate_report(share_email)