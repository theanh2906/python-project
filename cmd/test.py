import os
import sys
import threading
import time


def threads_example():
    threads = []
    for index in range(3):
        thread = threading.Thread(target=thread_function, args=(index,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print("All threads have finished execution.")
def thread_function(name):
    print(f'Thread {name}: starting')
    time.sleep(2)
    print(f'Thread {name}: finishing')
    print(f'Thread {name}: finishing')

def system_info():
    print("System Information:")
    print(f"Platform: {os.name}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")

if __name__ == '__main__':
    # threads_example()
    system_info()