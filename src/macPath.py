from pathlib import Path
import os
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
        os.makedirs(path)
    else:
        print(f"Folder already exists at {path}")

    return path