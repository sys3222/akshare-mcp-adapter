import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger("mcp-unified-service")

# Base directory for caching user files
CACHE_BASE_DIR = Path("static/cache")

def get_user_cache_dir(username: str) -> Path:
    """
    Constructs and creates the cache directory for a specific user.
    """
    if not username or ".." in username or "/" in username:
        raise HTTPException(status_code=400, detail="Invalid username.")
    
    user_dir = CACHE_BASE_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

async def save_uploaded_file(file: UploadFile, username: str) -> dict:
    """
    Saves an uploaded file to the user's specific cache directory.
    """
    user_dir = get_user_cache_dir(username)
    
    # Sanitize filename to prevent directory traversal
    filename = Path(file.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
        
    file_path = user_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"User '{username}' uploaded file '{filename}' to '{file_path}'.")
        return {"filename": filename, "detail": "File uploaded successfully."}
    except Exception as e:
        logger.error(f"Error saving file for user '{username}': {e}")
        raise HTTPException(status_code=500, detail="Could not save file.")

def list_user_files(username: str) -> list:
    """
    Lists all files in a user's cache directory.
    """
    user_dir = get_user_cache_dir(username)
    if not user_dir.exists():
        return []
    
    return sorted([f.name for f in user_dir.iterdir() if f.is_file()])

def delete_user_file(filename: str, username: str) -> dict:
    """
    Deletes a specific file from a user's cache directory.
    """
    user_dir = get_user_cache_dir(username)
    
    # Sanitize filename
    filename = Path(filename).name
    file_path = user_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
        
    # Final security check to ensure we are deleting from within the user's directory
    if not str(file_path.resolve()).startswith(str(user_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    try:
        file_path.unlink()
        logger.info(f"User '{username}' deleted file '{filename}'.")
        return {"filename": filename, "detail": "File deleted successfully."}
    except Exception as e:
        logger.error(f"Error deleting file '{filename}' for user '{username}': {e}")
        raise HTTPException(status_code=500, detail="Could not delete file.")

def get_user_file_path(filename: str, username: str) -> Path:
    """
    Safely gets the full path to a user's file.
    """
    user_dir = get_user_cache_dir(username)
    
    # Sanitize filename
    filename = Path(filename).name
    file_path = user_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
        
    return file_path
