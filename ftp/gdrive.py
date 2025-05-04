import os
import io
import logging
import json
import mimetypes
import traceback
from django.conf import settings
from django.utils import timezone

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.initialize_service()
    
    def initialize_service(self):
        """Initialize the Google Drive API service."""
        try:
            credentials_path = settings.GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE
            
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found at {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
                
            # Log the content of credentials file (with sensitive data redacted)
            try:
                with open(credentials_path, 'r') as f:
                    cred_data = json.load(f)
                    # Redact sensitive information for logging
                    if 'private_key' in cred_data:
                        cred_data['private_key'] = 'REDACTED'
                    if 'client_email' in cred_data:
                        logger.info(f"Using service account: {cred_data['client_email']}")
                    logger.debug(f"Credentials data structure: {json.dumps(cred_data, indent=2)}")
            except Exception as e:
                logger.warning(f"Could not parse credentials file for debugging: {e}")
            
            # Create credentials from service account file
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            # Test if service is working by listing files
            try:
                results = self.service.files().list(pageSize=5).execute()
                files = results.get('files', [])
                logger.info(f"Drive API connection successful. Found {len(files)} files.")
            except Exception as e:
                logger.error(f"Drive API connection test failed: {e}")
                logger.error(traceback.format_exc())
            
            logger.info("Google Drive service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
            logger.error(traceback.format_exc())
            self.service = None
    
    def create_user_folder(self, folder_name):
        """Create a folder in Google Drive for a user and return its ID."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created user folder {folder_name} with ID {folder_id}")
            return folder_id
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return None
    
    def create_subfolder(self, folder_name, parent_folder_id):
        """Create a subfolder in Google Drive and return its ID."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created subfolder {folder_name} with ID {folder_id} in parent {parent_folder_id}")
            return folder_id
        except Exception as e:
            logger.error(f"Error creating subfolder: {e}")
            return None
    
    def upload_file(self, file_path, file_name, parent_folder_id, share_with_email=None):
        """Upload a file to Google Drive and return its ID. Optionally share with an email."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            # Verify file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found at path: {file_path}")
                return None
                
            # Log file details
            file_size = os.path.getsize(file_path)
            logger.info(f"Uploading file: {file_name} ({file_size} bytes) from {file_path}")
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            logger.info(f"Using MIME type: {mime_type}")
            
            # Verify parent folder exists
            try:
                folder_check = self.service.files().get(fileId=parent_folder_id, fields="id,name").execute()
                logger.info(f"Parent folder verified: {folder_check.get('name')} ({parent_folder_id})")
            except Exception as e:
                logger.error(f"Parent folder validation failed: {str(e)}")
                # Create a root folder as fallback
                parent_folder_id = self.create_user_folder("gdriveftp_root_folder")
                logger.info(f"Created fallback root folder: {parent_folder_id}")
            
            # Create file metadata
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id],
                'description': f'Uploaded by GDriveFTP at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            logger.debug(f"File metadata: {file_metadata}")
            
            # Create media
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            # Execute the upload with progress reporting
            logger.info("Starting file upload...")
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,size,webViewLink'
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            # Log complete response
            logger.info(f"Upload complete: {response}")
            file_id = response.get('id')
            web_link = response.get('webViewLink', 'No web link available')
            logger.info(f"Uploaded file {file_name} with ID {file_id} to folder {parent_folder_id}")
            logger.info(f"File can be viewed at: {web_link}")
            
            # Share the file if an email is provided
            if share_with_email and file_id:
                try:
                    logger.info(f"Sharing file with: {share_with_email}")
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': share_with_email
                    }
                    share_result = self.service.permissions().create(
                        fileId=file_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=False
                    ).execute()
                    logger.info(f"Shared file {file_name} with {share_with_email}: {share_result}")
                except Exception as e:
                    logger.error(f"Error sharing file: {e}")
                    logger.error(traceback.format_exc())
            
            # Final verification - check if file exists
            try:
                verification = self.service.files().get(fileId=file_id, fields="id,name").execute()
                logger.info(f"File upload verified: {verification.get('name')} ({file_id})")
            except Exception as e:
                logger.error(f"File verification failed: {str(e)}")
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            logger.error(traceback.format_exc())
            return None
            
    def create_user_folder(self, folder_name, share_with_email=None):
        """Create a folder in Google Drive for a user and return its ID."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            logger.info(f"Creating user folder: {folder_name}")
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': f'Created by GDriveFTP at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            logger.debug(f"Folder metadata: {file_metadata}")
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            folder_id = folder.get('id')
            web_link = folder.get('webViewLink', 'No web link available')
            logger.info(f"Created user folder {folder_name} with ID {folder_id}")
            logger.info(f"Folder can be viewed at: {web_link}")
            
            # Share the folder if an email is provided
            if share_with_email and folder_id:
                try:
                    logger.info(f"Sharing folder with: {share_with_email}")
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': share_with_email
                    }
                    share_result = self.service.permissions().create(
                        fileId=folder_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=False
                    ).execute()
                    logger.info(f"Shared folder {folder_name} with {share_with_email}: {share_result}")
                except Exception as e:
                    logger.error(f"Error sharing folder: {e}")
                    logger.error(traceback.format_exc())
            
            # Verify folder was created
            try:
                verification = self.service.files().get(fileId=folder_id, fields="id,name").execute()
                logger.info(f"Folder creation verified: {verification.get('name')} ({folder_id})")
            except Exception as e:
                logger.error(f"Folder verification failed: {str(e)}")
            
            return folder_id
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def create_subfolder(self, folder_name, parent_folder_id, share_with_email=None):
        """Create a subfolder in Google Drive and return its ID."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            logger.info(f"Creating subfolder: {folder_name} in parent folder: {parent_folder_id}")
            
            # Verify parent folder exists
            try:
                parent_check = self.service.files().get(fileId=parent_folder_id, fields="id,name").execute()
                logger.info(f"Parent folder verified: {parent_check.get('name')} ({parent_folder_id})")
            except Exception as e:
                logger.error(f"Parent folder validation failed: {str(e)}")
                return None
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id],
                'description': f'Created by GDriveFTP at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            logger.debug(f"Subfolder metadata: {file_metadata}")
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            folder_id = folder.get('id')
            web_link = folder.get('webViewLink', 'No web link available')
            logger.info(f"Created subfolder {folder_name} with ID {folder_id} in parent {parent_folder_id}")
            logger.info(f"Subfolder can be viewed at: {web_link}")
            
            # Share the folder if an email is provided
            if share_with_email and folder_id:
                try:
                    logger.info(f"Sharing subfolder with: {share_with_email}")
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': share_with_email
                    }
                    share_result = self.service.permissions().create(
                        fileId=folder_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=False
                    ).execute()
                    logger.info(f"Shared subfolder {folder_name} with {share_with_email}: {share_result}")
                except Exception as e:
                    logger.error(f"Error sharing subfolder: {e}")
                    logger.error(traceback.format_exc())
            
            # Verify subfolder was created
            try:
                verification = self.service.files().get(fileId=folder_id, fields="id,name").execute()
                logger.info(f"Subfolder creation verified: {verification.get('name')} ({folder_id})")
            except Exception as e:
                logger.error(f"Subfolder verification failed: {str(e)}")
            
            return folder_id
        except Exception as e:
            logger.error(f"Error creating subfolder: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def download_file(self, file_id):
        """Download a file from Google Drive."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            file_content.seek(0)
            logger.info(f"Downloaded file with ID {file_id}")
            return file_content
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    def delete_file(self, file_id):
        """Delete a file from Google Drive."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file with ID {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def delete_folder(self, folder_id):
        """Delete a folder from Google Drive."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return False
        
        try:
            self.service.files().delete(fileId=folder_id).execute()
            logger.info(f"Deleted folder with ID {folder_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting folder: {e}")
            return False
    
    def list_files_and_folders(self, folder_id):
        """List all files and folders in a folder."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, mimeType, size, createdTime)"
            ).execute()
            
            items = results.get('files', [])
            logger.info(f"Listed {len(items)} items in folder {folder_id}")
            return items
        except Exception as e:
            logger.error(f"Error listing files and folders: {e}")
            return []
    
    def list_files(self, folder_id):
        """List all files in a folder."""
        items = self.list_files_and_folders(folder_id)
        return [item for item in items if item.get('mimeType') != 'application/vnd.google-apps.folder']
    
    def list_folders(self, folder_id):
        """List all subfolders in a folder."""
        items = self.list_files_and_folders(folder_id)
        return [item for item in items if item.get('mimeType') == 'application/vnd.google-apps.folder']