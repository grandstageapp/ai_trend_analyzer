#!/bin/bash
# Start the scheduler as a background process

echo "Starting AI Trends Analyzer Scheduler..."
cd /home/runner/workspace

# Kill any existing scheduler processes
pkill -f "python.*scheduler.py" 2>/dev/null || true

# Start the scheduler in the background
nohup python scheduler.py > scheduler.log 2>&1 &
SCHEDULER_PID=$!

echo "Scheduler started with PID: $SCHEDULER_PID"
echo "Logs are being written to scheduler.log"
echo "To stop the scheduler, run: kill $SCHEDULER_PID"

# Save PID for later reference
echo $SCHEDULER_PID > scheduler.pid

echo "Use 'tail -f scheduler.log' to monitor the scheduler"