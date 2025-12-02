import sys
import os
import queue
import time
import threading

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.tester import StressTester

def test_logic():
    print("Starting logic test...")
    
    # A: Generates a random number 1-10
    code_a = """
import random
print(random.randint(1, 10))
"""

    # B: Prints the number
    code_b = """
import sys
n = int(sys.stdin.read().strip())
print(n)
"""

    # C: Prints the number + 1 (Should fail)
    code_c = """
import sys
n = int(sys.stdin.read().strip())
if n > 5:
    print(n + 1)
else:
    print(n)
"""

    log_queue = queue.Queue()
    tester = StressTester(code_a, "python", code_b, "python", code_c, "python", log_queue, timeout=5) # Added timeout for consistency
    
    tester.start()
    
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            msg = log_queue.get(timeout=0.1)
            print(f"LOG: {msg}")
            if "Discrepancy found" in msg:
                print("TEST PASSED: Discrepancy found as expected.")
                tester.stop()
                return
        except queue.Empty:
            continue
    
    tester.stop()
    print("TEST FAILED: No discrepancy found within timeout.")

def test_tle():
    print("Starting TLE test...")

    # A: Simple generator
    code_a = """
print(1)
"""
    # B: Solution that will time out
    code_b_tle = """
import time
time.sleep(3) # Sleep for 3 seconds
print("Done")
"""
    # C: Simple solution
    code_c = """
import sys
print(sys.stdin.read().strip())
"""
    log_queue = queue.Queue()
    # Set a timeout of 1 second, so B should time out
    tester = StressTester(code_a, "python", code_b_tle, "python", code_c, "python", log_queue, timeout=1)

    tester.start()

    start_time = time.time()
    tle_detected = False
    while time.time() - start_time < 5: # Give it enough time to detect TLE
        try:
            msg = log_queue.get(timeout=0.1)
            print(f"LOG: {msg}")
            if "Solution B failed (Case 1):" in msg and "Error:\nTimeout" in msg:
                print("TEST PASSED: TLE detected for Solution B as expected.")
                tle_detected = True
                break
        except queue.Empty:
            continue
    
    tester.stop()
    if not tle_detected:
        print("TEST FAILED: TLE for Solution B not detected within timeout.")

if __name__ == "__main__":
    test_logic()
    print("\n")
    test_tle()
