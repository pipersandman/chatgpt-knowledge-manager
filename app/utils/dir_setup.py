import os
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def ensure_app_directories():
    """
    Ensure all required application directories exist
    Creates any missing directories needed for app operation
    """
    try:
        # Get project root directory
        root_dir = Path(__file__).parent.parent.parent
        
        # Define required directories with relative paths
        required_dirs = [
            "data",                  # For application data
            "exports",               # For data exports
            "app/frontend/static",   # For static files (CSS, JS)
            "logs"                   # For log files
        ]
        
        # Create directories if they don't exist
        for dir_path in required_dirs:
            full_path = root_dir / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            else:
                logger.debug(f"Directory exists: {full_path}")
        
        # Return success
        return True
    
    except Exception as e:
        logger.error(f"Error setting up directories: {e}")
        return False


def create_empty_init_files():
    """
    Create empty __init__.py files in all app directories to ensure proper imports
    """
    try:
        # Get project root directory
        root_dir = Path(__file__).parent.parent.parent
        app_dir = root_dir / "app"
        
        # Find all subdirectories
        subdirs = [app_dir] + [d for d in app_dir.glob("**") if d.is_dir()]
        
        # Create __init__.py in each directory if it doesn't exist
        for dir_path in subdirs:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                with open(init_file, 'w') as f:
                    # Leave file empty
                    pass
                logger.debug(f"Created __init__.py in {dir_path}")
        
        # Return success
        return True
    
    except Exception as e:
        logger.error(f"Error creating __init__.py files: {e}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # When run directly, set up directories and __init__ files
    print("Setting up application directories...")
    ensure_app_directories()
    
    print("Creating __init__.py files...")
    create_empty_init_files()
    
    print("Setup complete!")