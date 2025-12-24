"""
EC2 Configuration Loader for AWS Database Migration Analyzer
=============================================================
This module provides a Streamlit-secrets-compatible interface for EC2 deployments.
It loads configuration from environment variables, .env file, or JSON config files.

Usage:
    from ec2_config import secrets, load_ec2_config
    
    # Call at app startup
    load_ec2_config()
    
    # Use like Streamlit secrets
    if 'firebase' in secrets:
        project_id = secrets['firebase']['project_id']
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ec2_config')


class EC2Secrets:
    """
    A Streamlit-secrets-compatible configuration class for EC2 deployments.
    Loads configuration from environment variables, .env file, or JSON config.
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self, env_file: Optional[str] = None, config_file: Optional[str] = None):
        """Load configuration from multiple sources"""
        
        # Load from .env file if it exists
        env_paths = [
            env_file,
            '.env',
            '/etc/dbmigration/.env',
            os.path.expanduser('~/.dbmigration/.env'),
            '/opt/dbmigration/.env'
        ]
        
        for env_path in env_paths:
            if env_path and os.path.exists(env_path):
                self._load_env_file(env_path)
                logger.info(f"Loaded configuration from {env_path}")
                break
        
        # Load Firebase config from JSON file if exists
        firebase_paths = [
            config_file,
            'firebase-config.json',
            '/etc/dbmigration/firebase-config.json',
            os.path.expanduser('~/.dbmigration/firebase-config.json'),
            '/opt/dbmigration/firebase-config.json'
        ]
        
        for fb_path in firebase_paths:
            if fb_path and os.path.exists(fb_path):
                self._load_firebase_config(fb_path)
                logger.info(f"Loaded Firebase config from {fb_path}")
                break
        
        # Build Streamlit-compatible structure
        self._build_config()
        self._loaded = True
        
        return self
    
    def _load_env_file(self, filepath: str):
        """Parse and load a .env file"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except Exception as e:
            logger.warning(f"Could not load env file {filepath}: {e}")
    
    def _load_firebase_config(self, filepath: str):
        """Load Firebase service account JSON"""
        try:
            with open(filepath, 'r') as f:
                firebase_config = json.load(f)
                # Store in environment as JSON string
                os.environ['FIREBASE_CONFIG_JSON'] = json.dumps(firebase_config)
        except Exception as e:
            logger.warning(f"Could not load Firebase config {filepath}: {e}")
    
    def _build_config(self):
        """Build Streamlit-compatible secrets structure from environment variables"""
        
        # Anthropic API Key (top-level, as expected by the app)
        if os.getenv('ANTHROPIC_API_KEY'):
            self._config['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY')
        
        # Firebase Configuration
        firebase_config = {}
        
        # Try loading from JSON string first
        if os.getenv('FIREBASE_CONFIG_JSON'):
            try:
                firebase_config = json.loads(os.getenv('FIREBASE_CONFIG_JSON'))
            except json.JSONDecodeError:
                pass
        
        # Or build from individual environment variables
        if not firebase_config:
            firebase_env_mapping = {
                'type': 'FIREBASE_TYPE',
                'project_id': 'FIREBASE_PROJECT_ID',
                'private_key_id': 'FIREBASE_PRIVATE_KEY_ID',
                'private_key': 'FIREBASE_PRIVATE_KEY',
                'client_email': 'FIREBASE_CLIENT_EMAIL',
                'client_id': 'FIREBASE_CLIENT_ID',
                'auth_uri': 'FIREBASE_AUTH_URI',
                'token_uri': 'FIREBASE_TOKEN_URI',
                'auth_provider_x509_cert_url': 'FIREBASE_AUTH_PROVIDER_CERT_URL',
                'client_x509_cert_url': 'FIREBASE_CLIENT_CERT_URL',
                'web_api_key': 'FIREBASE_WEB_API_KEY'
            }
            
            for key, env_var in firebase_env_mapping.items():
                if os.getenv(env_var):
                    firebase_config[key] = os.getenv(env_var)
        
        if firebase_config:
            self._config['firebase'] = firebase_config
        
        # Admin Configuration
        admin_config = {}
        if os.getenv('ADMIN_EMAIL'):
            admin_config['email'] = os.getenv('ADMIN_EMAIL')
        if os.getenv('ADMIN_PASSWORD'):
            admin_config['password'] = os.getenv('ADMIN_PASSWORD')
        if os.getenv('ADMIN_KEY'):
            admin_config['key'] = os.getenv('ADMIN_KEY')
        
        if admin_config:
            self._config['admin'] = admin_config
        
        # AWS Configuration (for any AWS-specific settings)
        aws_config = {
            'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        }
        if os.getenv('AWS_ACCESS_KEY_ID'):
            aws_config['access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
            aws_config['secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        
        self._config['aws'] = aws_config
        
        # Application settings
        self._config['app'] = {
            'mode': os.getenv('APP_MODE', 'production'),
            'port': int(os.getenv('APP_PORT', '8501')),
            'host': os.getenv('APP_HOST', '0.0.0.0'),
            'debug': os.getenv('APP_DEBUG', 'false').lower() == 'true'
        }
    
    def __contains__(self, key: str) -> bool:
        """Support 'key in secrets' syntax"""
        if not self._loaded:
            self.load()
        return key in self._config
    
    def __getitem__(self, key: str) -> Any:
        """Support 'secrets[key]' syntax"""
        if not self._loaded:
            self.load()
        return self._config[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Support 'secrets.get(key, default)' syntax"""
        if not self._loaded:
            self.load()
        return self._config.get(key, default)
    
    def keys(self):
        """Return all configuration keys"""
        if not self._loaded:
            self.load()
        return self._config.keys()
    
    def items(self):
        """Return all configuration items"""
        if not self._loaded:
            self.load()
        return self._config.items()
    
    def __repr__(self):
        return f"EC2Secrets(loaded={self._loaded}, sections={list(self._config.keys())})"


# Global secrets instance
secrets = EC2Secrets()


def load_ec2_config(env_file: Optional[str] = None, config_file: Optional[str] = None) -> EC2Secrets:
    """
    Load EC2 configuration and set up environment.
    Call this at the start of your application.
    
    Args:
        env_file: Optional path to .env file
        config_file: Optional path to Firebase JSON config
    
    Returns:
        EC2Secrets instance
    """
    global secrets
    secrets.load(env_file, config_file)
    
    # Set AWS region as environment variable for boto3
    os.environ['AWS_DEFAULT_REGION'] = secrets['aws']['region']
    
    logger.info("EC2 configuration loaded successfully")
    logger.info(f"AWS Region: {secrets['aws']['region']}")
    logger.info(f"Firebase configured: {'firebase' in secrets}")
    logger.info(f"Anthropic API configured: {'ANTHROPIC_API_KEY' in secrets}")
    
    return secrets


def patch_streamlit_secrets():
    """
    Monkey-patch streamlit.secrets to use EC2 configuration.
    Call this before importing Streamlit in your main app.
    """
    try:
        import streamlit as st
        
        # Load EC2 config
        load_ec2_config()
        
        # Replace Streamlit's secrets with our EC2 secrets
        st.secrets = secrets
        
        logger.info("Streamlit secrets patched with EC2 configuration")
        return True
    except ImportError:
        logger.warning("Streamlit not installed, cannot patch secrets")
        return False


def check_configuration() -> Dict[str, Any]:
    """
    Verify configuration is complete.
    Returns status of each configuration section.
    """
    load_ec2_config()
    
    status = {
        'anthropic_api': 'ANTHROPIC_API_KEY' in secrets,
        'firebase': 'firebase' in secrets and bool(secrets.get('firebase', {}).get('project_id')),
        'admin': 'admin' in secrets and bool(secrets.get('admin', {}).get('email')),
        'aws_region': bool(secrets['aws']['region']),
    }
    
    return status


def print_config_status():
    """Print current configuration status for debugging"""
    load_ec2_config()
    
    print("\n" + "="*60)
    print("AWS Database Migration Analyzer - EC2 Configuration Status")
    print("="*60)
    
    print(f"\n📁 Configuration Sections: {list(secrets.keys())}")
    
    print(f"\n🤖 Anthropic AI:")
    if 'ANTHROPIC_API_KEY' in secrets:
        key = secrets['ANTHROPIC_API_KEY']
        print(f"   API Key: {key[:10]}...{key[-4:] if len(key) > 14 else ''}")
    else:
        print("   ❌ Not configured (AI features disabled)")
    
    print(f"\n🔥 Firebase:")
    if 'firebase' in secrets:
        fb = secrets['firebase']
        print(f"   Project ID: {fb.get('project_id', 'Not set')}")
        print(f"   Client Email: {fb.get('client_email', 'Not set')}")
        print(f"   Web API Key: {'✓ Set' if fb.get('web_api_key') else '✗ Not set'}")
    else:
        print("   ❌ Not configured (running in demo mode)")
    
    print(f"\n👤 Admin:")
    if 'admin' in secrets:
        admin = secrets['admin']
        print(f"   Email: {admin.get('email', 'Not set')}")
        print(f"   Password: {'✓ Set' if admin.get('password') else '✗ Not set'}")
    else:
        print("   ❌ Not configured")
    
    print(f"\n☁️  AWS:")
    print(f"   Region: {secrets['aws']['region']}")
    print(f"   Using IAM Role: {'access_key_id' not in secrets['aws']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print_config_status()
