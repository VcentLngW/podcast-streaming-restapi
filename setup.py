#!/usr/bin/env python3
"""
Setup script for the Podcast REST API
This script helps initialize the database and create necessary directories.
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories for the application."""
    print("Creating necessary directories...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Create instance directory for SQLite database
    instance_dir = project_root / "instance"
    instance_dir.mkdir(exist_ok=True)
    print(f"✓ Created instance directory: {instance_dir}")
    
    # Create upload directories
    upload_dir = project_root / "app" / "uploads"
    upload_dir.mkdir(exist_ok=True)
    print(f"✓ Created upload directory: {upload_dir}")
    
    audio_dir = upload_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    print(f"✓ Created audio directory: {audio_dir}")
    
    thumbnails_dir = upload_dir / "thumbnails"
    thumbnails_dir.mkdir(exist_ok=True)
    print(f"✓ Created thumbnails directory: {thumbnails_dir}")

def check_environment():
    """Check if environment variables are set up."""
    print("\nChecking environment setup...")
    
    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("⚠ .env file not found. Please copy env.example to .env and configure it.")
        return False
    
    return True

def main():
    """Main setup function."""
    print("=== Podcast REST API Setup ===\n")
    
    # Create directories
    create_directories()
    
    # Check environment
    env_ok = check_environment()
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Configure your .env file with proper values")
    print("2. Run: flask db upgrade")
    print("3. Run: python run.py")
    
    if not env_ok:
        print("\n⚠ Please set up your .env file before running the application.")
        sys.exit(1)

if __name__ == "__main__":
    main() 