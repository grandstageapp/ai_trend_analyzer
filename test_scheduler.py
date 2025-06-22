#!/usr/bin/env python3
"""
Test the scheduler functionality
"""
from scheduler import check_rate_limit_and_schedule
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

print("=== Testing Scheduler Functionality ===")
check_rate_limit_and_schedule()
print("=== Test Complete ===")