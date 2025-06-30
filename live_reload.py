# live_reload.py
import os
import subprocess
import sys
import time

filename = sys.argv[1] if len(sys.argv) > 1 else 'main.py'
last_mtime = None
proc = None

while True:
    mtime = os.path.getmtime(filename)
    language = filename.split('.').pop()
    # A dictionary to map file extensions to their start commands
    command = {
        'py': ['py', filename],
        'js': ['node', filename],
        'ts': ['node', filename],
        'java': ['java', filename],
        'go': ['go', 'run', filename],
    }
    if mtime != last_mtime:
        if proc:
            proc.terminate()
            proc.wait()
        print(f"\033[92mRestarting {filename}...\033[0m")
        proc = subprocess.Popen(command.get(language))
        last_mtime = mtime
    time.sleep(1)
