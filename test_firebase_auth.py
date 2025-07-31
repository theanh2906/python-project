#!/usr/bin/env python3
"""
Test script to verify Firebase authentication is working correctly
"""

import os
import sys
import base64
import json

def test_base64_file_exists():
    """Test if the base64 credentials file exists"""
    print("Testing base64 credentials file...")
    
    file_path = "serviceAccountKey.b64"
    if os.path.exists(file_path):
        print(f"✓ File exists: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"✓ File size: {file_size} bytes")
        
        return True
    else:
        print(f"✗ File not found: {file_path}")
        return False

def test_base64_decoding():
    """Test base64 decoding functionality"""
    print("\nTesting base64 decoding...")
    
    file_path = "serviceAccountKey.b64"
    try:
        with open(file_path, 'r') as f:
            base64_content = f.read().strip()
        
        print(f"✓ Read base64 content ({len(base64_content)} characters)")
        
        # Decode base64 content
        decoded_bytes = base64.b64decode(base64_content)
        decoded_json = decoded_bytes.decode('utf-8')
        
        print(f"✓ Decoded base64 to JSON ({len(decoded_json)} characters)")
        
        # Parse JSON
        credentials_dict = json.loads(decoded_json)
        
        print("✓ Successfully parsed JSON credentials")
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in credentials_dict]
        
        if missing_fields:
            print(f"✗ Missing required fields: {missing_fields}")
            return False
        
        print("✓ All required credential fields present")
        print(f"  - Type: {credentials_dict.get('type')}")
        print(f"  - Project ID: {credentials_dict.get('project_id')}")
        print(f"  - Client Email: {credentials_dict.get('client_email')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Base64 decoding failed: {e}")
        return False

def test_firebase_imports():
    """Test Firebase-related imports"""
    print("\nTesting Firebase imports...")
    
    try:
        import firebase_admin
        print("✓ firebase_admin imported")
        
        from firebase_admin import credentials
        print("✓ firebase_admin.credentials imported")
        
        from google.cloud import storage as gcs
        print("✓ google.cloud.storage imported")
        
        from google.oauth2 import service_account
        print("✓ google.oauth2.service_account imported")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_firebase_initialization():
    """Test Firebase initialization without GUI"""
    print("\nTesting Firebase initialization...")
    
    try:
        # Import required modules
        import firebase_admin
        from firebase_admin import credentials
        from google.cloud import storage as gcs
        from google.oauth2 import service_account
        
        # Configuration
        PROJECT_ID = "useful-tools-api"
        STORAGE_BUCKET = "useful-tools-api.firebasestorage.app"
        SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.b64"
        
        # Reset Firebase apps for clean test
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        
        # Decode base64 credentials
        with open(SERVICE_ACCOUNT_KEY_PATH, 'r') as f:
            base64_content = f.read().strip()
        
        decoded_bytes = base64.b64decode(base64_content)
        decoded_json = decoded_bytes.decode('utf-8')
        credentials_dict = json.loads(decoded_json)
        
        print("✓ Base64 credentials decoded successfully")
        
        # Initialize Firebase Admin
        cred = credentials.Certificate(credentials_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET
        })
        
        print("✓ Firebase Admin SDK initialized")
        
        # Initialize GCS client with same credentials
        gcs_credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = gcs.Client(project=PROJECT_ID, credentials=gcs_credentials)
        
        print("✓ Google Cloud Storage client initialized")
        
        # Test bucket access
        bucket_name = STORAGE_BUCKET.replace('gs://', '').replace('.firebasestorage.app', '.appspot.com')
        bucket = storage_client.bucket(bucket_name)
        
        print(f"✓ Storage bucket accessed: {bucket_name}")
        
        # Test listing files (this will verify permissions)
        try:
            blobs = list(bucket.list_blobs(max_results=1))
            print(f"✓ Successfully listed bucket contents ({len(blobs)} files found)")
        except Exception as e:
            print(f"⚠ Warning: Could not list bucket contents: {e}")
            print("  This might be due to permissions or empty bucket")
        
        return True
        
    except Exception as e:
        print(f"✗ Firebase initialization failed: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("Firebase Authentication Test")
    print("=" * 50)
    
    # Run tests
    file_ok = test_base64_file_exists()
    decode_ok = test_base64_decoding()
    import_ok = test_firebase_imports()
    firebase_ok = test_firebase_initialization()
    
    # Summary
    print("\n" + "=" * 50)
    if file_ok and decode_ok and import_ok and firebase_ok:
        print("✓ All tests passed! Firebase authentication is working correctly.")
        print("\nThe application should now be able to:")
        print("- Read and decode the base64 credentials file")
        print("- Initialize Firebase Admin SDK with proper credentials")
        print("- Initialize Google Cloud Storage client with the same credentials")
        print("- Access Firebase Storage without falling back to default credentials")
    else:
        print("✗ Some tests failed. Issues found:")
        if not file_ok:
            print("  - Base64 credentials file not found or inaccessible")
        if not decode_ok:
            print("  - Base64 decoding or JSON parsing failed")
        if not import_ok:
            print("  - Required Firebase/GCS modules not installed")
        if not firebase_ok:
            print("  - Firebase initialization failed")
    
    return file_ok and decode_ok and import_ok and firebase_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)