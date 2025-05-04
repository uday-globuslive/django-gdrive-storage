# Google Drive Integration Debugging Guide

If you're experiencing issues with files not showing up in Google Drive, follow this debugging guide.

## Prerequisites

1. Make sure you have a valid `credentials.json` file in the project root directory
2. Ensure your Google Drive API is enabled in your Google Cloud Console
3. Verify that your service account has the correct permissions

## Testing Google Drive Integration

### 1. Run the Test Script

We've provided a test script to directly test Google Drive integration:

```bash
cd /path/to/gdriveftp
source venv/bin/activate
python ftp/test_drive.py
```

This script will:
- Create a small test file
- Upload it to a test folder in Google Drive
- Log detailed information about the process

Look for messages like "Test file uploaded successfully" and "Google Drive API is working correctly!" in the output.

### 2. Check the Logs

The application generates detailed logs in `debug.log`. Look for error messages related to:

- Authentication issues
- Permission problems
- Network connectivity
- API responses

### 3. Verify Google Drive API Settings

Make sure your Google Cloud project has:

1. Google Drive API enabled
2. Service account with the "Storage Admin" or similar role
3. No domain restrictions that prevent file creation

### 4. Check Your Drive Access Method

There are three ways to see files uploaded by the application:

1. **Service Account Drive**: Files are stored under the service account's storage
2. **Shared With Me**: Files should appear in your "Shared with me" section if you've entered your email in Settings
3. **Direct Link**: Check the file URLs in the debug log and try accessing them directly

## Common Issues and Solutions

### 1. Authentication Errors

**Symptoms**: Error messages about invalid credentials or authentication failures

**Solutions**:
- Regenerate your `credentials.json` file from Google Cloud Console
- Ensure the service account has the correct Drive API scope
- Check file permissions on `credentials.json` (should be readable by the app)

### 2. Permission Errors

**Symptoms**: Files upload successfully but aren't visible to you

**Solutions**:
- Go to Settings and enter your Google email address
- Check spam/junk folder for sharing notifications
- Verify that sharing permissions work in your organization (some G Suite configurations restrict external sharing)

### 3. Quota or Rate Limit Errors

**Symptoms**: Uploads fail with quota or rate limit errors

**Solutions**:
- Check your Google Cloud Console for quota usage
- Enable billing if needed for higher quotas
- Implement retries with exponential backoff for failed requests

## Getting More Help

If you still have issues after following this guide, please:

1. Collect the complete `debug.log` file
2. Note any error messages displayed in the console or browser
3. Provide details about your Google Drive and Google Cloud configuration

With this information, we can provide more specific assistance with your Google Drive integration.