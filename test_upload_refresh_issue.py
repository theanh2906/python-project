#!/usr/bin/env python3
"""
Test script to reproduce and debug the upload and refresh issues
in the Firebase Storage Management application.
"""

import os
import sys
import base64
import json
import tempfile
from datetime import datetime

def test_firebase_connection():
    """Test Firebase Storage connection and basic operations"""
    print("Testing Firebase Storage connection...")
    
    try:
        # Import required modules
        import firebase_admin
        from firebase_admin import credentials
        from google.cloud import storage as gcs
        from google.oauth2 import service_account
        
        # Configuration (same as in the main app)
        PROJECT_ID = "useful-tools-api"
        STORAGE_BUCKET = "useful-tools-api.firebasestorage.app"
        SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.b64"
        
        print(f"✓ Project ID: {PROJECT_ID}")
        print(f"✓ Storage Bucket: {STORAGE_BUCKET}")
        print(f"✓ Credentials file: {SERVICE_ACCOUNT_KEY_PATH}")
        
        # Reset Firebase apps for clean test
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        
        # Initialize Firebase (same logic as main app)
        if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            # Decode base64 credentials
            with open(SERVICE_ACCOUNT_KEY_PATH, 'r') as f:
                base64_content = f.read().strip()
            
            decoded_bytes = base64.b64decode(base64_content)
            decoded_json = decoded_bytes.decode('utf-8')
            credentials_dict = json.loads(decoded_json)
            
            # Initialize Firebase Admin
            cred = credentials.Certificate(credentials_dict)
            firebase_admin.initialize_app(cred, {
                'storageBucket': STORAGE_BUCKET
            })
            
            # Initialize GCS client with same credentials
            gcs_credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            storage_client = gcs.Client(project=PROJECT_ID, credentials=gcs_credentials)
            
            print("✓ Firebase Admin and GCS client initialized")
        else:
            print(f"✗ Credentials file not found: {SERVICE_ACCOUNT_KEY_PATH}")
            return False
        
        # Test different bucket name formats
        bucket_formats = [
            STORAGE_BUCKET,  # Original: useful-tools-api.firebasestorage.app
            STORAGE_BUCKET.replace('.firebasestorage.app', '.appspot.com'),  # Converted: useful-tools-api.appspot.com
            STORAGE_BUCKET.replace('gs://', '').replace('.firebasestorage.app', '.appspot.com')  # Main app logic
        ]
        
        working_bucket = None
        for bucket_name in bucket_formats:
            try:
                print(f"\n🧪 Testing bucket format: {bucket_name}")
                bucket = storage_client.bucket(bucket_name)
                
                # Try to list files (this will test if bucket exists and we have access)
                blobs = list(bucket.list_blobs(max_results=1))
                print(f"✓ Successfully accessed bucket: {bucket_name}")
                print(f"✓ Found {len(blobs)} files in bucket")
                working_bucket = bucket
                break
                
            except Exception as e:
                print(f"✗ Failed to access bucket {bucket_name}: {e}")
        
        if not working_bucket:
            print("✗ No working bucket format found!")
            return False
        
        # Test upload functionality
        print(f"\n🧪 Testing upload functionality...")
        test_content = f"Test file created at {datetime.now()}"
        test_filename = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            # Create temporary test file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            # Upload test file
            blob = working_bucket.blob(test_filename)
            blob.upload_from_filename(temp_file_path)
            print(f"✓ Successfully uploaded test file: {test_filename}")
            
            # Verify upload by listing files
            blobs = list(working_bucket.list_blobs(prefix=test_filename))
            if blobs:
                print(f"✓ Upload verified - file found in bucket")
                
                # Download and verify content
                downloaded_content = blobs[0].download_as_text()
                if downloaded_content == test_content:
                    print(f"✓ Content verification passed")
                else:
                    print(f"✗ Content verification failed")
                
                # Clean up test file
                blobs[0].delete()
                print(f"✓ Test file cleaned up")
            else:
                print(f"✗ Upload verification failed - file not found in bucket")
            
            # Clean up local temp file
            os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"✗ Upload test failed: {e}")
            return False
        
        # Test refresh functionality
        print(f"\n🧪 Testing refresh functionality...")
        try:
            all_blobs = list(working_bucket.list_blobs())
            print(f"✓ Successfully listed all files: {len(all_blobs)} files found")
            
            for i, blob in enumerate(all_blobs[:3]):  # Show first 3 files
                print(f"  File {i+1}: {blob.name} ({blob.size} bytes)")
            
            if len(all_blobs) > 3:
                print(f"  ... and {len(all_blobs) - 3} more files")
                
        except Exception as e:
            print(f"✗ Refresh test failed: {e}")
            return False
        
        print(f"\n✅ All tests passed! Firebase Storage is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def test_main_app_issues():
    """Test for specific issues in the main application"""
    print(f"\n" + "="*60)
    print("TESTING MAIN APPLICATION ISSUES")
    print("="*60)
    
    # Check if the main app can be imported
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from firebase_storage_management import FirebaseStorageManager
        print("✓ Main application can be imported")
        
        # Check bucket name transformation logic
        app_storage_bucket = "useful-tools-api.firebasestorage.app"
        transformed_bucket = app_storage_bucket.replace('gs://', '').replace('.firebasestorage.app', '.appspot.com')
        
        print(f"📋 Bucket name transformation analysis:")
        print(f"  Original: {app_storage_bucket}")
        print(f"  Transformed: {transformed_bucket}")
        
        if app_storage_bucket != transformed_bucket:
            print(f"⚠️  POTENTIAL ISSUE: Bucket name is being transformed!")
            print(f"     This might cause upload/refresh failures if the transformed name is incorrect.")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to import main application: {e}")
        return False

def main():
    """Run all tests"""
    print("Firebase Storage Upload/Refresh Issue Test")
    print("=" * 60)
    
    # Test Firebase connection and operations
    firebase_ok = test_firebase_connection()
    
    # Test main app issues
    app_ok = test_main_app_issues()
    
    # Summary
    print(f"\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if firebase_ok and app_ok:
        print("✅ Firebase Storage connection and operations are working correctly.")
        print("\nIf uploads/refresh still don't work in the main app, the issue might be:")
        print("1. Bucket name transformation (check the bucket format being used)")
        print("2. Threading/timing issues (refresh called too quickly after upload)")
        print("3. UI update issues (tree not refreshing properly)")
        print("4. Error handling masking the real issue")
    else:
        print("❌ Issues found:")
        if not firebase_ok:
            print("  - Firebase Storage connection or operations failed")
        if not app_ok:
            print("  - Main application import or analysis failed")
    
    return firebase_ok and app_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)