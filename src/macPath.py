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
    print("Locating or creating app folder in .../AppData/Local")
    home_dir = Path.home()
    path = home_dir / "AppData" / "Local" / "GradeSync"  # Ensure the GradeSync folder is included

    try:
        if not os.path.exists(path):
            print(f"Creating directory at {path}")
            os.makedirs(path, mode=0o666)  # Create the directory with appropriate permissions
            print("Making directory")
            print(path)
            return path
        else:
            print(f"Folder already exists at {path}")
            return path
    except Exception as e:
        print(f"Failed to create directory {path}: {e}")