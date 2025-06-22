#!/usr/bin/env python3
"""
Entry point to run the scheduler as a background process
"""
import subprocess
import sys
import os
import signal
import time
from pathlib import Path

def run_scheduler():
    """Run the scheduler in the background"""
    try:
        # Change to the project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        # Start the scheduler process
        print("Starting AI Trends Scheduler...")
        process = subprocess.Popen([
            sys.executable, "scheduler.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        print(f"Scheduler started with PID: {process.pid}")
        print("Press Ctrl+C to stop the scheduler")
        
        # Monitor the process
        try:
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"[SCHEDULER] {output.strip()}")
                elif process.poll() is not None:
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            process.terminate()
            process.wait()
            print("Scheduler stopped")
            
    except Exception as e:
        print(f"Error running scheduler: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_scheduler())