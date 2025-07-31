"""
Firebase Storage Management GUI Tool

A modern Python GUI application for managing Firebase Storage with features including:
- File and folder display with tree view
- Upload/download functionality
- Delete with PIN confirmation
- Zip and upload capabilities
- Modern UI with customtkinter

INSTALLATION REQUIREMENTS:
1. Install required packages:
   pip install customtkinter firebase-admin pillow python-dateutil

2. Firebase Setup:
   - Create a Firebase project at https://console.firebase.google.com/
   - Enable Firebase Storage in your project
   - Go to Project Settings > Service Accounts
   - Generate a new private key (JSON file)
   - Save the JSON file and update the SERVICE_ACCOUNT_KEY_PATH variable below
   - OR set GOOGLE_APPLICATION_CREDENTIALS environment variable to the JSON file path
   - Update PROJECT_ID and STORAGE_BUCKET variables with your project details
   
   CREDENTIAL FILE FORMATS SUPPORTED:
   - Regular JSON files (.json): Standard Firebase service account key files
   - Base64 encoded files (.b64): JSON credentials encoded in base64 format
   - Auto-detection: The app will automatically detect the file format

3. Update deletion PIN if desired (default: "1402")

FEATURES IMPLEMENTED:
✓ Modern dark theme UI with customtkinter
✓ Hierarchical tree view for files and folders
✓ File upload with progress tracking
✓ Folder upload with recursive file handling
✓ Zip and upload with smart naming (device-timestamp or folder name)
✓ Delete with PIN confirmation and double verification
✓ Real-time status updates and progress bars
✓ Loading states to prevent multiple operations
✓ Comprehensive error handling
✓ Threading to prevent GUI freezing
✓ Responsive design with proper grid layouts

Author: Firebase Storage Management Tool
Date: 2025-07-31
"""

import base64
import json
import os
import platform
import tempfile
import threading
import zipfile
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog

import customtkinter as ctk
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage as gcs
from google.cloud.exceptions import NotFound, Forbidden, Unauthorized

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class FirebaseStorageManager:
    def __init__(self):
        """Initialize the Firebase Storage Manager application"""
        
        # Firebase configuration for firebase-admin
        # Update these values with your Firebase project details
        self.PROJECT_ID = "useful-tools-api"
        self.STORAGE_BUCKET = "useful-tools-api.firebasestorage.app"
        
        # Path to service account key file (supports both .json and .b64 files)
        # You can also set GOOGLE_APPLICATION_CREDENTIALS environment variable instead
        self.SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.json"
        
        # PIN for deletion confirmation
        self.deletion_pin = "1402"
        
        # Loading state (initialize early to prevent AttributeError)
        self.is_loading = False
        
        # Initialize Firebase
        self.storage_client = None
        self.bucket = None
        self.init_firebase()
        
        # Initialize GUI
        self.root = ctk.CTk()
        self.setup_gui()
        
        # Storage for current files and folders
        self.current_files = {}
        self.selected_items = []
        
    def decode_base64_credentials(self, file_path):
        """Decode base64 encoded service account credentials file"""
        try:
            with open(file_path, 'r') as f:
                base64_content = f.read().strip()
            
            # Decode base64 content
            decoded_bytes = base64.b64decode(base64_content)
            decoded_json = decoded_bytes.decode('utf-8')
            
            # Parse JSON to verify it's valid
            credentials_dict = json.loads(decoded_json)
            
            print(f"[DEBUG] Successfully decoded base64 credentials from {file_path}")
            return credentials_dict
            
        except Exception as e:
            print(f"[ERROR] Failed to decode base64 credentials: {e}")
            raise Exception(f"Failed to decode base64 credentials from {file_path}: {e}")
    
    def init_firebase(self):
        """Initialize Firebase connection using firebase-admin"""
        try:
            # Store credentials for both Firebase Admin and GCS client
            gcs_credentials = None
            
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                # Try to use service account key file if it exists
                if os.path.exists(self.SERVICE_ACCOUNT_KEY_PATH):
                    try:
                        # Check file extension to determine how to load credentials
                        if self.SERVICE_ACCOUNT_KEY_PATH.lower().endswith('.b64'):
                            # Decode base64 encoded credentials
                            credentials_dict = self.decode_base64_credentials(self.SERVICE_ACCOUNT_KEY_PATH)
                            cred = credentials.Certificate(credentials_dict)
                            # Create GCS credentials from the same dictionary
                            from google.oauth2 import service_account
                            gcs_credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                            print("[DEBUG] Using base64 decoded credentials")
                        elif self.SERVICE_ACCOUNT_KEY_PATH.lower().endswith('.json'):
                            # Load regular JSON credentials file
                            cred = credentials.Certificate(self.SERVICE_ACCOUNT_KEY_PATH)
                            # Create GCS credentials from the same file
                            from google.oauth2 import service_account
                            gcs_credentials = service_account.Credentials.from_service_account_file(self.SERVICE_ACCOUNT_KEY_PATH)
                            print("[DEBUG] Using JSON credentials file")
                        else:
                            # Try to auto-detect by attempting JSON first, then base64
                            try:
                                cred = credentials.Certificate(self.SERVICE_ACCOUNT_KEY_PATH)
                                from google.oauth2 import service_account
                                gcs_credentials = service_account.Credentials.from_service_account_file(self.SERVICE_ACCOUNT_KEY_PATH)
                                print("[DEBUG] Using credentials file (detected as JSON)")
                            except Exception:
                                # If JSON fails, try base64 decoding
                                credentials_dict = self.decode_base64_credentials(self.SERVICE_ACCOUNT_KEY_PATH)
                                cred = credentials.Certificate(credentials_dict)
                                from google.oauth2 import service_account
                                gcs_credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                                print("[DEBUG] Using credentials file (detected as base64)")
                        
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': self.STORAGE_BUCKET
                        })
                        print("[DEBUG] Firebase initialized with service account key")
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to load service account credentials: {e}")
                        raise Exception(f"Failed to load credentials from {self.SERVICE_ACCOUNT_KEY_PATH}: {e}")
                else:
                    # Try to use application default credentials (environment variable)
                    try:
                        firebase_admin.initialize_app()
                        print("[DEBUG] Firebase initialized with application default credentials")
                        # For GCS, let it use default credentials too
                        gcs_credentials = None
                    except Exception as e:
                        print(f"[WARNING] Could not initialize with default credentials: {e}")
                        # Initialize without credentials (will need to be set via environment)
                        firebase_admin.initialize_app()
                        print("[DEBUG] Firebase initialized without explicit credentials")
                        gcs_credentials = None
            
            # Get storage client and bucket with proper credentials
            if gcs_credentials:
                self.storage_client = gcs.Client(project=self.PROJECT_ID, credentials=gcs_credentials)
                print("[DEBUG] GCS client initialized with service account credentials")
            else:
                self.storage_client = gcs.Client(project=self.PROJECT_ID)
                print("[DEBUG] GCS client initialized with default credentials")
            
            # Try different bucket name formats for compatibility
            bucket_name = self.STORAGE_BUCKET.replace('gs://', '')
            
            # First try the original bucket name (for newer Firebase projects)
            try:
                self.bucket = self.storage_client.bucket(bucket_name)
                # Test bucket access
                list(self.bucket.list_blobs(max_results=1))
                print(f"[DEBUG] Using bucket name: {bucket_name}")
            except Exception as e:
                print(f"[DEBUG] Failed to access bucket {bucket_name}: {e}")
                # Fallback to .appspot.com format (for older Firebase projects)
                try:
                    bucket_name_appspot = bucket_name.replace('.firebasestorage.app', '.appspot.com')
                    self.bucket = self.storage_client.bucket(bucket_name_appspot)
                    # Test bucket access
                    list(self.bucket.list_blobs(max_results=1))
                    print(f"[DEBUG] Using fallback bucket name: {bucket_name_appspot}")
                except Exception as e2:
                    print(f"[ERROR] Failed to access both bucket formats: {e2}")
                    raise Exception(f"Cannot access Firebase Storage bucket. Tried: {bucket_name}, {bucket_name_appspot}")
            
            print("[DEBUG] Firebase Storage initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Firebase: {e}")
            messagebox.showerror("Firebase Error", 
                f"Failed to initialize Firebase: {e}\n\n"
                f"Please ensure:\n"
                f"1. Service account key file exists at: {self.SERVICE_ACCOUNT_KEY_PATH}\n"
                f"   (Supports both .json and .b64 base64-encoded files)\n"
                f"2. OR set GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
                f"3. Project ID and Storage Bucket are correct\n"
                f"4. If using .b64 file, ensure it contains valid base64-encoded JSON credentials\n"
                f"5. Ensure the service account has proper permissions for Firebase Storage")
    
    def setup_gui(self):
        """Setup the main GUI components"""
        self.root.title("Firebase Storage Manager")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Create header frame
        self.create_header()
        
        # Create main content frame
        self.create_main_content()
        
        # Create footer frame
        self.create_footer()
        
        # Load initial data
        self.refresh_storage()
    
    def create_header(self):
        """Create the header with title and action buttons"""
        header_frame = ctk.CTkFrame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Firebase Storage Manager", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Action buttons frame
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Refresh",
            command=self.refresh_storage,
            width=100,
            height=35
        )
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Upload file button
        self.upload_file_btn = ctk.CTkButton(
            buttons_frame,
            text="📁 Upload Files",
            command=self.upload_files,
            width=120,
            height=35
        )
        self.upload_file_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Upload folder button (now includes zip functionality)
        self.upload_folder_btn = ctk.CTkButton(
            buttons_frame,
            text="📂 Upload Folder (Zip)",
            command=self.upload_folder,
            width=140,
            height=35
        )
        self.upload_folder_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Delete button
        self.delete_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete",
            command=self.delete_selected,
            width=100,
            height=35,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.grid(row=0, column=3)
    
    def create_main_content(self):
        """Create the main content area with file tree and details"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # File tree frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(1, weight=1)
        
        # Tree label
        tree_label = ctk.CTkLabel(
            tree_frame, 
            text="Files and Folders", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tree_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create treeview with custom styling
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure treeview colors for dark theme with larger font
        style.configure("Treeview",
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0,
                       font=('Segoe UI', 11))  # Increased font size for better readability
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       borderwidth=1,
                       font=('Segoe UI', 11, 'bold'))  # Larger font for headers
        style.map("Treeview",
                 background=[('selected', '#1f538d')])
        
        # Configure modern scrollbar styling
        style.configure("Vertical.TScrollbar",
                       background="#3a3a3a",
                       troughcolor="#2b2b2b",
                       bordercolor="#2b2b2b",
                       arrowcolor="white",
                       darkcolor="#3a3a3a",
                       lightcolor="#4a4a4a")
        style.configure("Horizontal.TScrollbar",
                       background="#3a3a3a",
                       troughcolor="#2b2b2b",
                       bordercolor="#2b2b2b",
                       arrowcolor="white",
                       darkcolor="#3a3a3a",
                       lightcolor="#4a4a4a")
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("size", "modified", "type"),
            show="tree headings",
            selectmode="extended"
        )
        
        # Configure columns
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="center")
        self.tree.heading("modified", text="Modified", anchor="center")
        self.tree.heading("type", text="Type", anchor="center")
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("size", width=100, minwidth=80)
        self.tree.column("modified", width=150, minwidth=120)
        self.tree.column("type", width=80, minwidth=60)
        
        # Add scrollbars
        tree_scrollbar_v = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        # Grid treeview and scrollbars
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_scrollbar_v.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        tree_scrollbar_h.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Details frame
        details_frame = ctk.CTkFrame(main_frame)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Details label
        details_label = ctk.CTkLabel(
            details_frame, 
            text="Selection Details", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        details_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Details text widget
        self.details_text = ctk.CTkTextbox(
            details_frame,
            width=300,
            height=200,
            font=ctk.CTkFont(size=12)
        )
        self.details_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    def create_footer(self):
        """Create the footer with status and progress"""
        footer_frame = ctk.CTkFrame(self.root)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(footer_frame)
        self.progress_bar.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)
    
    def update_status(self, message, progress=None):
        """Update status message and progress bar"""
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress)
        self.root.update_idletasks()
    
    def set_loading_state(self, loading):
        """Enable/disable buttons during loading operations"""
        self.is_loading = loading
        state = "disabled" if loading else "normal"
        
        self.refresh_btn.configure(state=state)
        self.upload_file_btn.configure(state=state)
        self.upload_folder_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        
        if loading:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.set(0)
    
    def refresh_storage(self):
        """Refresh the file list from Firebase Storage"""
        if self.is_loading:
            return
            
        def refresh_thread():
            try:
                self.set_loading_state(True)
                self.update_status("Refreshing storage...")
                
                # Clear current tree
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                self.current_files = {}
                
                # Get all files from Firebase Storage using Google Cloud Storage
                try:
                    # List all blobs (files) in the bucket
                    blobs = self.bucket.list_blobs()
                    
                    for blob in blobs:
                        file_path = blob.name
                        
                        # Get file metadata from blob properties
                        try:
                            # Get file size
                            size = blob.size if blob.size else 0
                            size_str = self.format_file_size(size)
                            
                            # Get modification time
                            if blob.time_created:
                                modified_str = blob.time_created.strftime("%Y-%m-%d %H:%M")
                            elif blob.updated:
                                modified_str = blob.updated.strftime("%Y-%m-%d %H:%M")
                            else:
                                modified_str = "Unknown"
                            
                        except Exception as e:
                            print(f"[WARNING] Could not get metadata for {file_path}: {e}")
                            size_str = "Unknown"
                            modified_str = "Unknown"
                        
                        # Store file info
                        self.current_files[file_path] = {
                            'size': size_str,
                            'modified': modified_str,
                            'type': 'File',
                            'path': file_path,
                            'blob': blob  # Store blob reference for later operations
                        }
                        
                        # Add to tree
                        self.add_file_to_tree(file_path, size_str, modified_str)
                    
                    self.update_status(f"Loaded {len(self.current_files)} files")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to list files: {e}")
                    self.update_status("Failed to load files")
                    messagebox.showerror("Error", f"Failed to load files: {e}")
                
            except Exception as e:
                print(f"[ERROR] Refresh failed: {e}")
                self.update_status("Refresh failed")
                messagebox.showerror("Error", f"Refresh failed: {e}")
            finally:
                self.set_loading_state(False)
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def add_file_to_tree(self, file_path, size, modified):
        """Add a file to the tree view with proper folder structure"""
        path_parts = file_path.split('/')
        current_parent = ""
        
        # Create folder structure
        for i, part in enumerate(path_parts[:-1]):
            current_path = '/'.join(path_parts[:i+1])
            
            # Check if folder already exists
            folder_exists = False
            for item in self.tree.get_children(current_parent):
                if self.tree.item(item)['text'] == part:
                    current_parent = item
                    folder_exists = True
                    break
            
            if not folder_exists:
                # Create folder node
                folder_item = self.tree.insert(
                    current_parent, 
                    'end', 
                    text=part,
                    values=("", "", "Folder"),
                    tags=("folder",)
                )
                current_parent = folder_item
        
        # Add file
        file_name = path_parts[-1]
        self.tree.insert(
            current_parent,
            'end',
            text=file_name,
            values=(size, modified, "File"),
            tags=("file",)
        )
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def on_tree_select(self, event):
        """Handle tree selection changes"""
        selected_items = self.tree.selection()
        self.selected_items = selected_items
        
        if not selected_items:
            self.details_text.delete("1.0", "end")
            return
        
        # Update details panel
        details = f"Selected {len(selected_items)} item(s):\n\n"
        
        for item in selected_items[:5]:  # Show details for first 5 items
            item_text = self.tree.item(item)['text']
            item_values = self.tree.item(item)['values']
            
            details += f"Name: {item_text}\n"
            if len(item_values) >= 3:
                details += f"Size: {item_values[0]}\n"
                details += f"Modified: {item_values[1]}\n"
                details += f"Type: {item_values[2]}\n"
            details += "\n"
        
        if len(selected_items) > 5:
            details += f"... and {len(selected_items) - 5} more items"
        
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", details)
    
    def upload_files(self):
        """Upload selected files to Firebase Storage"""
        if self.is_loading:
            return
        
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            filetypes=[("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        def upload_thread():
            try:
                self.set_loading_state(True)
                total_files = len(file_paths)
                successful_uploads = 0
                
                for i, file_path in enumerate(file_paths):
                    file_name = os.path.basename(file_path)
                    # Calculate progress more accurately
                    current_progress = (i / total_files) if total_files > 0 else 0
                    self.update_status(f"Uploading {file_name}... ({i+1}/{total_files})", current_progress)
                    
                    try:
                        # Upload file to Firebase Storage using Google Cloud Storage
                        blob = self.bucket.blob(file_name)
                        print(f"[DEBUG] Starting upload of {file_name} (size: {os.path.getsize(file_path)} bytes)")
                        blob.upload_from_filename(file_path)
                        print(f"[DEBUG] Successfully uploaded: {file_name}")
                        
                        # Verify upload immediately
                        if blob.exists():
                            print(f"[DEBUG] Upload verified: {file_name} exists in bucket")
                            successful_uploads += 1
                        else:
                            print(f"[WARNING] Upload verification failed: {file_name} not found in bucket")
                            
                    except Exception as e:
                        print(f"[ERROR] Failed to upload {file_name}: {e}")
                        print(f"[ERROR] Error type: {type(e).__name__}")
                        messagebox.showerror("Upload Error", f"Failed to upload {file_name}: {e}")
                
                # Show completion with 100% progress
                self.update_status(f"Successfully uploaded {successful_uploads}/{total_files} files", 1.0)
                messagebox.showinfo("Success", f"Successfully uploaded {successful_uploads} out of {total_files} files")
                
                # Wait a moment for uploads to be fully committed
                import time
                time.sleep(1)
                
                # Refresh the file list
                print("[DEBUG] Refreshing file list after upload...")
                self.refresh_storage()
                
            except Exception as e:
                print(f"[ERROR] Upload failed: {e}")
                self.update_status("Upload failed")
                messagebox.showerror("Error", f"Upload failed: {e}")
            finally:
                self.set_loading_state(False)
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def upload_folder(self):
        """Upload a folder as a zip file to Firebase Storage"""
        if self.is_loading:
            return
        
        folder_path = filedialog.askdirectory(title="Select folder to zip and upload")
        
        if not folder_path:
            return
        
        def upload_folder_thread():
            try:
                self.set_loading_state(True)
                folder_name = os.path.basename(folder_path)
                
                self.update_status("Creating zip file...", 0.1)
                
                # Generate zip filename using folder name
                zip_filename = f"{folder_name}.zip"
                
                # Create temporary zip file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                    temp_zip_path = temp_zip.name
                
                try:
                    # Count total files for progress tracking
                    total_files = 0
                    for root, dirs, files in os.walk(folder_path):
                        total_files += len(files)
                    
                    self.update_status(f"Zipping {total_files} files...", 0.2)
                    
                    # Create zip file with folder contents
                    files_processed = 0
                    with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Create archive name relative to the selected folder
                                arcname = os.path.join(folder_name, os.path.relpath(file_path, folder_path))
                                # Convert Windows path separators to forward slashes
                                arcname = arcname.replace(os.sep, '/')
                                zipf.write(file_path, arcname)
                                files_processed += 1
                                
                                # Update progress during zipping
                                zip_progress = 0.2 + (files_processed / total_files) * 0.3  # 20% to 50%
                                self.update_status(f"Zipping... ({files_processed}/{total_files})", zip_progress)
                                
                                print(f"[DEBUG] Added file to zip: {arcname}")
                    
                    self.update_status(f"Uploading {zip_filename}...", 0.6)
                    
                    # Upload zip file to Firebase Storage
                    blob = self.bucket.blob(zip_filename)
                    print(f"[DEBUG] Starting upload of {zip_filename} (size: {os.path.getsize(temp_zip_path)} bytes)")
                    blob.upload_from_filename(temp_zip_path)
                    print(f"[DEBUG] Successfully uploaded: {zip_filename}")
                    
                    # Verify upload immediately
                    if blob.exists():
                        print(f"[DEBUG] Upload verified: {zip_filename} exists in bucket")
                        self.update_status(f"Successfully uploaded {zip_filename}", 1.0)
                    else:
                        print(f"[WARNING] Upload verification failed: {zip_filename} not found in bucket")
                        self.update_status(f"Upload verification failed for {zip_filename}", 1.0)
                    
                    messagebox.showinfo("Success", f"Successfully zipped and uploaded folder '{folder_name}' as {zip_filename}")
                    
                    # Wait a moment for uploads to be fully committed
                    import time
                    time.sleep(1)
                    
                    # Refresh the file list
                    print("[DEBUG] Refreshing file list after folder zip upload...")
                    self.refresh_storage()
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_zip_path)
                    except:
                        pass
                
            except Exception as e:
                print(f"[ERROR] Folder zip and upload failed: {e}")
                self.update_status("Folder zip and upload failed")
                messagebox.showerror("Error", f"Folder zip and upload failed: {e}")
            finally:
                self.set_loading_state(False)
        
        threading.Thread(target=upload_folder_thread, daemon=True).start()
    
    
    def delete_selected(self):
        """Delete selected files/folders with PIN confirmation"""
        if self.is_loading or not self.selected_items:
            return
        
        # PIN confirmation dialog
        pin = simpledialog.askstring(
            "Confirm Deletion",
            f"Enter PIN to delete {len(self.selected_items)} selected item(s):",
            show='*'
        )
        
        if pin != self.deletion_pin:
            messagebox.showerror("Invalid PIN", "Incorrect PIN entered. Deletion cancelled.")
            return
        
        # Final confirmation
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(self.selected_items)} selected item(s)?\n\nThis action cannot be undone."
        ):
            return
        
        def delete_thread():
            try:
                self.set_loading_state(True)
                deleted_count = 0
                total_items = len(self.selected_items)
                
                for i, item in enumerate(self.selected_items):
                    item_text = self.tree.item(item)['text']
                    item_values = self.tree.item(item)['values']
                    
                    self.update_status(f"Deleting {item_text}... ({i+1}/{total_items})", (i+1)/total_items)
                    
                    # Get full path for the item
                    full_path = self.get_item_full_path(item)
                    
                    if len(item_values) >= 3 and item_values[2] == "File":
                        # Delete file using Google Cloud Storage
                        try:
                            blob = self.bucket.blob(full_path)
                            blob.delete()
                            deleted_count += 1
                            print(f"[DEBUG] Deleted file: {full_path}")
                        except NotFound:
                            print(f"[WARNING] File not found (already deleted?): {full_path}")
                            # Don't show error for files that don't exist
                        except (Forbidden, Unauthorized) as e:
                            print(f"[ERROR] Permission denied to delete {full_path}: {e}")
                            messagebox.showerror("Permission Error", f"Permission denied to delete {full_path}")
                        except Exception as e:
                            print(f"[ERROR] Failed to delete {full_path}: {e}")
                            messagebox.showerror("Delete Error", f"Failed to delete {full_path}: {e}")
                    else:
                        # Delete folder (delete all files in folder)
                        try:
                            # Find all files that start with this folder path
                            files_to_delete = []
                            for file_path in self.current_files.keys():
                                if file_path.startswith(full_path + "/"):
                                    files_to_delete.append(file_path)
                            
                            for file_path in files_to_delete:
                                try:
                                    blob = self.bucket.blob(file_path)
                                    blob.delete()
                                    print(f"[DEBUG] Deleted file in folder: {file_path}")
                                except NotFound:
                                    print(f"[WARNING] File not found (already deleted?): {file_path}")
                                    # Don't show error for files that don't exist
                                except (Forbidden, Unauthorized) as e:
                                    print(f"[ERROR] Permission denied to delete {file_path}: {e}")
                                    messagebox.showerror("Permission Error", f"Permission denied to delete {file_path}")
                                except Exception as e:
                                    print(f"[ERROR] Failed to delete {file_path}: {e}")
                                    messagebox.showerror("Delete Error", f"Failed to delete {file_path}: {e}")
                            
                            deleted_count += len(files_to_delete)
                            
                        except Exception as e:
                            print(f"[ERROR] Failed to delete folder {full_path}: {e}")
                            messagebox.showerror("Delete Error", f"Failed to delete folder {full_path}: {e}")
                
                self.update_status(f"Successfully deleted {deleted_count} items")
                messagebox.showinfo("Success", f"Successfully deleted {deleted_count} items")
                
                # Refresh the file list
                self.refresh_storage()
                
            except Exception as e:
                print(f"[ERROR] Delete operation failed: {e}")
                self.update_status("Delete operation failed")
                messagebox.showerror("Error", f"Delete operation failed: {e}")
            finally:
                self.set_loading_state(False)
        
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def get_item_full_path(self, item):
        """Get the full path of a tree item"""
        path_parts = []
        current_item = item
        
        while current_item:
            item_text = self.tree.item(current_item)['text']
            path_parts.insert(0, item_text)
            current_item = self.tree.parent(current_item)
        
        return '/'.join(path_parts)
    
    def run(self):
        """Start the application"""
        print("[DEBUG] Starting Firebase Storage Manager...")
        self.root.mainloop()

def main():
    """Main function to run the application"""
    try:
        app = FirebaseStorageManager()
        app.run()
    except Exception as e:
        print(f"[ERROR] Application failed to start: {e}")
        messagebox.showerror("Startup Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()