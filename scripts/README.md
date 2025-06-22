# Scripts Directory

This directory contains utility scripts, test files, and development tools for the AI Trends Analyzer project.

## Test Scripts

### Phase 2 Architecture Testing
- `test_phase2_architecture.py` - Comprehensive test suite for Phase 2 architecture improvements
- `test_phase2_interactive.py` - Interactive demonstration of Phase 2 features

### Application Testing
- `test_app.py` - Basic application functionality tests
- `test_content_generation.py` - Content generation service tests
- `test_data_collection.py` - Data collection functionality tests
- `test_scheduler.py` - Scheduler functionality tests

## Utility Scripts

### Data Management
- `manual_data_collection.py` - Manual data collection for testing
- `populate_sample_data.py` - Sample data population for development

### System Management
- `start_scheduler.sh` - Shell script to start the background scheduler

## Usage

All scripts should be run from the project root directory:

```bash
# Run Phase 2 architecture tests
python scripts/test_phase2_interactive.py

# Run comprehensive test suite
python scripts/test_phase2_architecture.py

# Populate sample data
python scripts/populate_sample_data.py

# Manual data collection
python scripts/manual_data_collection.py
```

## Important Notes

- These scripts are for development, testing, and utility purposes
- Main application files remain in the root directory as expected by the application
- All scripts maintain their original functionality and dependencies