#!/usr/bin/env python3
"""
Test script to verify the Firebase Storage Management conversion from pyrebase to firebase-admin
"""

import sys
import os

def test_imports():
    """Test that all required imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        import customtkinter as ctk
        print("✓ customtkinter imported successfully")
        
        import firebase_admin
        print("✓ firebase_admin imported successfully")
        
        from firebase_admin import credentials, storage
        print("✓ firebase_admin.credentials and storage imported successfully")
        
        from google.cloud import storage as gcs
        print("✓ google.cloud.storage imported successfully")
        
        from google.cloud.exceptions import NotFound, Forbidden, Unauthorized
        print("✓ google.cloud.exceptions imported successfully")
        
        from google.api_core import exceptions as gcs_exceptions
        print("✓ google.api_core.exceptions imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_class_structure():
    """Test that the FirebaseStorageManager class can be imported and instantiated"""
    print("\nTesting class structure...")
    
    try:
        # Import the main module
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Try to import the class (but don't instantiate to avoid Firebase connection)
        from firebase_storage_management import FirebaseStorageManager
        print("✓ FirebaseStorageManager class imported successfully")
        
        # Check if key methods exist
        methods_to_check = [
            'init_firebase',
            'setup_gui', 
            'refresh_storage',
            'upload_files',
            'upload_folder',
            'zip_and_upload',
            'delete_selected'
        ]
        
        for method in methods_to_check:
            if hasattr(FirebaseStorageManager, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Class structure error: {e}")
        return False

def main():
    """Run all tests"""
    print("Firebase Storage Management - Conversion Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test class structure
    structure_ok = test_class_structure()
    
    # Summary
    print("\n" + "=" * 50)
    if imports_ok and structure_ok:
        print("✓ All tests passed! Conversion appears successful.")
        print("\nNext steps:")
        print("1. Install required packages: pip install firebase-admin google-cloud-storage")
        print("2. Set up Firebase service account credentials")
        print("3. Update PROJECT_ID and STORAGE_BUCKET in the code")
        print("4. Test the application with actual Firebase project")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return imports_ok and structure_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)