import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename):
    """Generate a unique filename using UUID and timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{timestamp}_{unique_id}.{ext}"

def save_file(file, folder, allowed_extensions):
    """Save an uploaded file to the specified folder"""
    if file and allowed_file(file.filename, allowed_extensions):
        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)
        
        # Generate secure and unique filename
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        
        # Save the file
        file_path = os.path.join(folder, unique_filename)
        file.save(file_path)
        
        # Return the relative path for storage in database
        return os.path.join(folder, unique_filename)
    return None

def delete_file(file_path):
    """Delete a file if it exists"""
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False 