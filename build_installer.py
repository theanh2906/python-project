#!/usr/bin/env python

import os
import subprocess
import sys


def main():
    # Check if at least one argument is provided
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <python_file_path> <comma_separated_binary_files>")
        print("  <python_file_path>: Path to the main Python script")
        print("  <comma_separated_binary_files>: Optional comma-separated list of binary files to include")
        sys.exit(1)

    # Get the Python file path
    python_file = sys.argv[1]

    # Check if the Python file exists
    if not os.path.isfile(python_file):
        print(f"Error: Python file '{python_file}' not found.")
        sys.exit(1)

    # Initialize PyInstaller command
    pyinstaller_cmd = ["pyinstaller", "--onefile", "--clean", "--noconsole"]

    # Process binary files if provided
    if len(sys.argv) > 2:
        binary_files = sys.argv[2]
        
        # Split the comma-separated list
        binaries = [b.strip() for b in binary_files.split(',')]
        
        # Add each binary file to the PyInstaller command
        for binary in binaries:
            if not os.path.isfile(binary):
                print(f"Warning: Binary file '{binary}' not found. Skipping.")
                continue
            
            # Add binary to PyInstaller command
            pyinstaller_cmd.extend(["--add-binary", f"{binary};."])
            print(f"Adding binary: {binary}")

    # Add the Python file to the command
    pyinstaller_cmd.append(python_file)

    # Display the command
    print(f"Executing: {' '.join(pyinstaller_cmd)}")

    # Run PyInstaller
    result = subprocess.run(pyinstaller_cmd)

    # Check if PyInstaller succeeded
    if result.returncode == 0:
        print("Build completed successfully!")
        
        # Get the executable name (based on the Python filename without extension)
        exe_name = os.path.splitext(os.path.basename(python_file))[0]
        
        # Print output location
        print(f"Executable created at: {os.path.join(os.getcwd(), 'dist', exe_name)}.exe")
    else:
        print("Build failed. See error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
