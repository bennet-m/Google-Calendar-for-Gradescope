from pathlib import Path
import os

#logger
import logging
logger = logging.getLogger(__name__)

def get_path():
    """Returns the path to the Application Support directory for your app."""
    home_dir = Path.home()
    path = home_dir / "Library" / "Application Support" / "gradeSync"
    # Create the directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True)  
    return path

def get_win_path():
    home_dir = Path.home()
    path = home_dir / "AppData" / "Local"
    if not os.path.exists(path):
        mode = 0o666
        os.makedirs(path, mode)
    else:
        logger.info(f"Folder already exists at {path}")

    return path