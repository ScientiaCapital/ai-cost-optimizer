#!/bin/bash
# Test script for Cost Optimization Agent

# Navigate to agent directory
cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Load environment variables
export $(grep -v '^#' ../.env | xargs 2>/dev/null || true)

# Run test
python3 test_agent.py
