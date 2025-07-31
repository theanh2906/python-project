#!/usr/bin/env python3
"""
Test script to verify base64 credential decoding functionality
"""

import base64
import json
import os

def test_base64_decoding():
    """Test the base64 decoding functionality"""
    print("Testing base64 credential decoding...")
    
    # Path to the base64 encoded credentials file
    b64_file_path = "serviceAccountKey.b64"
    
    if not os.path.exists(b64_file_path):
        print(f"✗ File not found: {b64_file_path}")
        return False
    
    try:
        # Read the base64 content
        with open(b64_file_path, 'r') as f:
            base64_content = f.read().strip()
        
        print(f"✓ Successfully read base64 file ({len(base64_content)} characters)")
        
        # Decode base64 content
        decoded_bytes = base64.b64decode(base64_content)
        decoded_json = decoded_bytes.decode('utf-8')
        
        print(f"✓ Successfully decoded base64 content ({len(decoded_json)} characters)")
        
        # Parse JSON to verify it's valid
        credentials_dict = json.loads(decoded_json)
        
        print("✓ Successfully parsed JSON credentials")
        
        # Verify required fields are present
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key', 
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in credentials_dict:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"✗ Missing required fields: {missing_fields}")
            return False
        
        print("✓ All required credential fields are present")
        
        # Display some basic info (without sensitive data)
        print(f"  - Type: {credentials_dict.get('type', 'N/A')}")
        print(f"  - Project ID: {credentials_dict.get('project_id', 'N/A')}")
        print(f"  - Client Email: {credentials_dict.get('client_email', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during decoding: {e}")
        return False

def test_firebase_storage_manager_import():
    """Test importing the FirebaseStorageManager class"""
    print("\nTesting FirebaseStorageManager import...")
    
    try:
        from firebase_storage_management import FirebaseStorageManager
        print("✓ Successfully imported FirebaseStorageManager")
        
        # Check if the decode_base64_credentials method exists
        if hasattr(FirebaseStorageManager, 'decode_base64_credentials'):
            print("✓ decode_base64_credentials method exists")
        else:
            print("✗ decode_base64_credentials method not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def main():
    """Run all tests"""
    print("Base64 Credentials Test")
    print("=" * 40)
    
    # Test base64 decoding
    decoding_ok = test_base64_decoding()
    
    # Test class import
    import_ok = test_firebase_storage_manager_import()
    
    # Summary
    print("\n" + "=" * 40)
    if decoding_ok and import_ok:
        print("✓ All tests passed! Base64 credential support is working.")
        print("\nThe Firebase Storage Manager should now be able to:")
        print("- Read and decode the serviceAccountKey.b64 file")
        print("- Parse the decoded JSON credentials")
        print("- Initialize Firebase with the decoded credentials")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return decoding_ok and import_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)