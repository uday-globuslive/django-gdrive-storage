from django.contrib import admin
from .models import UserProfile, FileEntry

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved', 'created_at', 'updated_at')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'user__email')
    actions = ['approve_users', 'revoke_users']
    
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} users have been approved.")
    approve_users.short_description = "Approve selected users"
    
    def revoke_users(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} users have been revoked.")
    revoke_users.short_description = "Revoke selected users"

@admin.register(FileEntry)
class FileEntryAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'file_size', 'upload_date')
    list_filter = ('upload_date',)
    search_fields = ('file_name', 'user__username')