import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """
    Set up the application environment before running
    """
    try:
        # Import directory setup utility
        from app.utils.dir_setup import ensure_app_directories, create_empty_init_files
        
        # Ensure directories exist
        ensure_app_directories()
        
        # Create __init__.py files
        create_empty_init_files()
        
        # Check for .env file
        env_file = Path('.env')
        env_template = Path('.env.template')
        
        if not env_file.exists() and env_template.exists():
            logger.warning(".env file not found. Creating from template.")
            
            # Copy template to .env
            with open(env_template, 'r') as template:
                with open(env_file, 'w') as env:
                    env.write(template.read())
            
            logger.info("Created .env file from template. Please edit with your configuration.")
    
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")


def run_app():
    """
    Run the Streamlit application
    """
    try:
        # Set up environment
        setup_environment()
        
        # Run Streamlit app
        logger.info("Starting AI Knowledge Manager application...")
        
        # Command to run Streamlit
        cmd = ["streamlit", "run", "app.py"]
        
        # Run the app
        subprocess.run(cmd)
    
    except Exception as e:
        logger.error(f"Error running application: {e}")


if __name__ == "__main__":
    run_app()