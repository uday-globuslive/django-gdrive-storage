from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_approved = models.BooleanField(default=False)
    drive_folder_id = models.CharField(max_length=255, blank=True, null=True)
    share_email = models.EmailField(blank=True, null=True, help_text="Your personal Google email to share files with")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

class FolderEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    folder_name = models.CharField(max_length=255)
    drive_folder_id = models.CharField(max_length=255)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.folder_name} - {self.user.username}"
    
    def get_path(self):
        """Get the full path of the folder."""
        if self.parent_folder is None:
            return self.folder_name
        return f"{self.parent_folder.get_path()}/{self.folder_name}"
    
    class Meta:
        ordering = ['folder_name']
        verbose_name_plural = 'Folder entries'

class FileEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    drive_file_id = models.CharField(max_length=255)
    upload_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    folder = models.ForeignKey(FolderEntry, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    
    def __str__(self):
        return f"{self.file_name} - {self.user.username}"
    
    def get_path(self):
        """Get the full path of the file."""
        if self.folder is None:
            return self.file_name
        return f"{self.folder.get_path()}/{self.file_name}"
    
    class Meta:
        ordering = ['-upload_date']