# 📝 Obsidian Notes Uploader

A beautiful CLI tool for zipping and uploading your Obsidian notes from `C:\Notes` to Firebase Storage with hardcoded credentials and rich terminal interface.

## ✨ Features

- 🎨 **Beautiful CLI Interface** - Rich terminal UI with progress bars, panels, and colored output
- 📦 **Smart Zipping** - Efficiently compresses your entire Obsidian vault
- 🔥 **Firebase Integration** - Direct upload to Firebase Storage
- 🔐 **Hardcoded Credentials** - No need for external credential files
- 📊 **Progress Tracking** - Real-time progress bars for zipping and uploading
- 📈 **Statistics Display** - Shows file counts, sizes, and upload metrics
- ⚡ **Fast & Reliable** - Optimized compression and upload process

## 🚀 Installation

1. **Install Dependencies**:

   ```bash
   pip install -r obsidian_uploader_requirements.txt
   ```

2. **Configure Credentials**:
   Edit the `SERVICE_ACCOUNT_CREDENTIALS` dictionary in `obsidian_notes_uploader.py` with your Firebase service account details:

   ```python
   self.SERVICE_ACCOUNT_CREDENTIALS = {
       "type": "service_account",
       "project_id": "your-project-id",
       "private_key_id": "your-private-key-id",
       "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
       "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
       "client_id": "your-client-id",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
   }
   ```

3. **Update Project Settings**:
   ```python
   self.PROJECT_ID = "your-firebase-project-id"
   self.STORAGE_BUCKET = "your-project.firebasestorage.app"
   ```

## 🎯 Usage

Simply run the tool:

```bash
python tools/obsidian_notes_uploader.py
```

The tool will:

1. 🔍 Scan your `C:\Notes` directory
2. 📊 Display statistics (file count, total size, markdown files)
3. 🔗 Connect to Firebase Storage
4. ❓ Ask for confirmation to proceed
5. 📦 Create a timestamped zip file
6. ⬆️ Upload to Firebase Storage
7. ✅ Show upload summary with metrics

## 📋 Requirements

- **Python 3.7+**
- **Obsidian notes** located in `C:\Notes`
- **Firebase project** with Storage enabled
- **Service account** with Storage permissions

## 🎨 Interface Preview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📝 Obsidian Notes Uploader v1.0    🔥 Firebase Storage Integration    2024-01-15 │
│ 📁 Source: C:\Notes                                                    PID: 1234 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────── 📊 Obsidian Notes Information ───────────────────────┐
│ 📁 Directory:      C:\Notes                                             │
│ 📄 Total Files:    1,247                                               │
│ 📝 Markdown Files: 892                                                 │
│ 💾 Total Size:     45.2 MB                                             │
│ 🕒 Last Modified:  2024-01-15 14:30:25                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Options

You can modify these settings in the script:

- **Notes Directory**: Change `self.notes_directory` to point to your Obsidian vault
- **Compression Level**: Modify `compresslevel=6` in `zipfile.ZipFile()` (1-9)
- **File Naming**: Customize the timestamp format in `zip_filename`

## 📦 Output

The tool creates zip files with a fixed name:

- `Notes.zip`

Each zip contains your entire Obsidian vault structure preserved.

## 🛡️ Security Notes

- **Hardcoded Credentials**: For production use, consider using environment variables
- **Private Keys**: Ensure your service account has minimal required permissions
- **Network**: Tool requires internet connection for Firebase upload

## 🐛 Troubleshooting

**Directory Not Found**:

- Ensure `C:\Notes` exists and contains your Obsidian vault
- Update `self.notes_directory` if your vault is elsewhere

**Firebase Connection Issues**:

- Verify your service account credentials are correct
- Check that Firebase Storage is enabled in your project
- Ensure the service account has Storage Admin permissions

**Upload Failures**:

- Check your internet connection
- Verify bucket name format (`.firebasestorage.app` vs `.appspot.com`)
- Ensure sufficient storage quota in Firebase

## 📄 License

This tool is part of the python-project toolkit for personal productivity automation.
