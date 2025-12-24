#!/usr/bin/env python3
"""
AWS Database Migration Analyzer - EC2 Streamlit Launcher
=========================================================
This is the entry point for running the application on EC2.
It patches Streamlit secrets with EC2-compatible configuration before 
importing and running the main application.

Usage:
    streamlit run streamlit_app_ec2.py --server.port 8501 --server.address 0.0.0.0
"""

import os
import sys
from pathlib import Path

# Ensure the application directory is in the Python path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# ============================================================
# STEP 1: Load EC2 Configuration BEFORE importing Streamlit
# ============================================================
from ec2_config import load_ec2_config, secrets

# Load configuration from environment or .env file
config = load_ec2_config()

# Set Anthropic API key as environment variable
if 'ANTHROPIC_API_KEY' in config:
    os.environ['ANTHROPIC_API_KEY'] = config['ANTHROPIC_API_KEY']

# Set AWS region
os.environ['AWS_DEFAULT_REGION'] = config['aws']['region']

# ============================================================
# STEP 2: Now import Streamlit and patch secrets
# ============================================================
import streamlit as st

# Monkey-patch Streamlit secrets with our EC2 configuration
st.secrets = secrets

# ============================================================
# STEP 3: Run the main application by importing it
# ============================================================

# Import the main streamlit_app module
# This will execute the app since it has top-level code
import streamlit_app
