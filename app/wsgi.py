import sys
import logging
import os

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)
logging.debug(f"Project directory added to path: {project_dir}")

try:
    # Import the 'app' Flask instance from app.py
    from app import app
    # Import the SecretManagerDB class from secret_manager.py
    from secret_manager import SecretManagerDB # <-- ADD THIS LINE

    # Initialize secret_manager here, where mod_wsgi loads the application
    # This ensures 'secret_manager' is always defined in the correct scope.
    secret_manager_instance = SecretManagerDB() # <-- ADD THIS LINE

    # Attach the secret_manager instance to the Flask app object
    app.secret_manager = secret_manager_instance # <-- ADD THIS LINE
    
    # Set the WSGI callable as Flask expects
    application = app # <-- ENSURE THIS IS 'app' AND NOT 'app as application' in the import

    logging.debug("Flask application and secret_manager initialized successfully in wsgi.py.")

except Exception as e:
    logging.error(f"Error during WSGI script initialization: {e}", exc_info=True)
    raise # Re-raise to crash early and show in logs
