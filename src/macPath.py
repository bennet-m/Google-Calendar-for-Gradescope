from pathlib import Path

def get_path():
    """Returns the path to the Application Support directory for your app."""
    home_dir = Path.home()
    path = home_dir / "Library" / "Application Support" / "gradeSync"
    # Create the directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True)  
    return path