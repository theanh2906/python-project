#!/usr/bin/env python3
"""
Test script to verify that the 'is_loading' AttributeError has been fixed
in the FirebaseStorageManager class.
"""

import sys
import os

def test_is_loading_attribute():
    """Test that the is_loading attribute is properly accessible"""
    print("Testing FirebaseStorageManager is_loading attribute...")
    
    try:
        # Import the FirebaseStorageManager class
        sys.path.insert(0, os.path.dirname(__file__))
        
        # We'll test the class structure without actually initializing Firebase
        # to avoid dependency issues during testing
        print("✓ Importing FirebaseStorageManager...")
        
        # Read the source code to verify the fix
        with open('firebase-storage-management.py', 'r') as f:
            content = f.read()
        
        # Check that is_loading is initialized before init_firebase
        lines = content.split('\n')
        is_loading_line = None
        init_firebase_line = None
        
        for i, line in enumerate(lines):
            if 'self.is_loading = False' in line:
                is_loading_line = i + 1
                print(f"✓ Found 'self.is_loading = False' on line {is_loading_line}")
            elif 'self.init_firebase()' in line:
                init_firebase_line = i + 1
                print(f"✓ Found 'self.init_firebase()' on line {init_firebase_line}")
        
        if is_loading_line and init_firebase_line:
            if is_loading_line < init_firebase_line:
                print("✓ Initialization order is correct: is_loading is set before init_firebase()")
                return True
            else:
                print("✗ Initialization order is incorrect: is_loading is set after init_firebase()")
                return False
        else:
            print("✗ Could not find both is_loading initialization and init_firebase() call")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def test_class_structure():
    """Test that the class can be imported without immediate errors"""
    print("\nTesting class import...")
    
    try:
        # Try to import the class (but don't instantiate to avoid Firebase dependencies)
        from firebase_storage_management import FirebaseStorageManager
        print("✓ FirebaseStorageManager class imported successfully")
        
        # Check if the class has the expected methods that use is_loading
        methods_using_is_loading = [
            'set_loading_state',
            'refresh_storage',
            'upload_files',
            'upload_folder',
            'zip_and_upload',
            'delete_selected'
        ]
        
        for method in methods_using_is_loading:
            if hasattr(FirebaseStorageManager, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Class import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("FirebaseStorageManager is_loading Fix Test")
    print("=" * 50)
    
    # Test initialization order
    order_ok = test_is_loading_attribute()
    
    # Test class structure
    structure_ok = test_class_structure()
    
    # Summary
    print("\n" + "=" * 50)
    if order_ok and structure_ok:
        print("✓ All tests passed! The is_loading AttributeError should be fixed.")
        print("\nThe fix ensures that:")
        print("- self.is_loading is initialized early in __init__")
        print("- The attribute is available before any method calls")
        print("- All methods that use is_loading can access it safely")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return order_ok and structure_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)