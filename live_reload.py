# live_reload.py
import glob
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional


def show_help():
    """Display help information for the live_reload tool."""
    help_text = """
Live Reload Tool - Automatically restart your script when files change

Usage:
    py live_reload.py <file_to_run> [watch_pattern]

Arguments:
    file_to_run       The file to execute when changes are detected
    watch_pattern     (Optional) Pattern of files to watch for changes
                      If not provided, only the file_to_run will be watched
                      Examples: "*.py", "src/*.js", "**/*.py"

Options:
    -h, --help        Show this help message and exit

Supported file extensions:
    .py               Python files (executed with 'py')
    .js, .ts          JavaScript/TypeScript files (executed with 'node')
    .java             Java files (executed with 'java')
    .go               Go files (executed with 'go run')

Examples:
    py live_reload.py main.py                # Watch and execute main.py
    py live_reload.py main.py "*.py"         # Execute main.py when any .py file changes
    py live_reload.py app.js "src/*.js"      # Execute app.js when any .js file in src changes
    py live_reload.py server.py "**/*.py"    # Execute server.py when any .py file changes recursively
    """
    print(help_text)
    sys.exit(0)

def find_files_by_pattern(pattern: str) -> List[str]:
    """
    Find all files matching the given pattern.

    Args:
        pattern: File pattern to match (e.g., '*.py', 'tools/*.py')

    Returns:
        List of file paths matching the pattern
    """
    # Handle patterns with and without directory separators
    if '**' in pattern:
        # Pattern already has recursive wildcard
        return glob.glob(pattern, recursive=True)
    elif os.path.sep in pattern:
        # Pattern has directory separator but no recursive wildcard
        return glob.glob(pattern)
    else:
        # Pattern is for current directory only (e.g., '*.py')
        return glob.glob(pattern)

def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.

    Args:
        filename: Name of the file

    Returns:
        File extension without the dot
    """
    return filename.split('.')[-1]

# Check for help flags
if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
    show_help()

# Get the file to run (first argument)
if len(sys.argv) > 1:
    file_to_run = sys.argv[1]
else:
    file_to_run = 'main.py'

# Check if the file to run exists
if not os.path.exists(file_to_run):
    print(f"\033[91mError: File to run '{file_to_run}' not found\033[0m")
    sys.exit(1)

# Get the watch pattern (second argument)
if len(sys.argv) > 2:
    watch_pattern = sys.argv[2]
    # If the pattern contains wildcard characters, find all matching files
    if '*' in watch_pattern:
        files_to_watch = find_files_by_pattern(watch_pattern)
        if not files_to_watch:
            print(f"\033[93mWarning: No files found matching pattern '{watch_pattern}'\033[0m")
            print(f"Watching only the file to run: '{file_to_run}'")
            files_to_watch = [file_to_run]
    else:
        # If no wildcard, treat as a single file to watch
        files_to_watch = [watch_pattern]
else:
    # If no watch pattern provided, only watch the file to run
    files_to_watch = [file_to_run]

# Dictionary to store the last modification time for each file
last_mtimes: Dict[str, Optional[float]] = {file: None for file in files_to_watch}
proc = None
main_file = file_to_run  # The file to run is specified by the first argument

print(f"\033[94mWatching {len(files_to_watch)} file(s): {', '.join(files_to_watch)}\033[0m")

while True:
    # Check if any of the watched files has changed
    file_changed = False
    for file in files_to_watch:
        try:
            mtime = os.path.getmtime(file)
            if last_mtimes[file] is None or mtime != last_mtimes[file]:
                last_mtimes[file] = mtime
                file_changed = True
                print(f"\033[96mFile changed: {file}\033[0m")
        except FileNotFoundError:
            # If file is deleted, remove it from the watch list
            print(f"\033[93mWarning: File not found: {file}\033[0m")
            files_to_watch.remove(file)
            del last_mtimes[file]
            if not files_to_watch:
                print("\033[91mNo files left to watch. Exiting...\033[0m")
                sys.exit(1)
            # If the file to run is deleted, exit the program
            if file == main_file:
                print(f"\033[91mError: File to run '{main_file}' was deleted. Exiting...\033[0m")
                sys.exit(1)

    if file_changed:
        language = get_file_extension(main_file)
        # A dictionary to map file extensions to their start commands
        command = {
            'py': ['py', main_file],
            'js': ['node', main_file],
            'ts': ['node', main_file],
            'java': ['java', main_file],
            'go': ['go', 'run', main_file],
        }

        if proc:
            proc.terminate()
            proc.wait()

        print(f"\033[92mRestarting {main_file}...\033[0m")
        proc = subprocess.Popen(command.get(language))

    time.sleep(1)
