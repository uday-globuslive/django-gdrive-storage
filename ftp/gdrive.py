import os
import io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from django.conf import settings
import mimetypes

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
            if os.path.exists(credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=self.credentials)
                logger.info("Google Drive service initialized successfully")
            else:
                logger.error(f"Credentials file not found at {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
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
    
    def upload_file(self, file_path, file_name, parent_folder_id):
        """Upload a file to Google Drive and return its ID."""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Uploaded file {file_name} with ID {file_id} to folder {parent_folder_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
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