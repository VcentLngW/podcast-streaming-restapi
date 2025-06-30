import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Static file URL configuration
    STATIC_FILE_URL = os.getenv('STATIC_FILE_URL', 'http://localhost:5000/')
    
    # Other configurations
    # ... existing code ... 