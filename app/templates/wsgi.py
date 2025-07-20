import sys
import logging
import os # Added for path handling

# Log to stderr, which Apache captures in its error.log
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Add your project directory to the Python path
project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)
logging.debug(f"Project directory added to path: {project_dir}")

# Import your Flask application instance
try:
    from app import app as application
    logging.debug("Flask application imported successfully.")
except Exception as e:
    logging.error(f"Error importing Flask application: {e}")
    raise # Re-raise to crash early and show in logs
