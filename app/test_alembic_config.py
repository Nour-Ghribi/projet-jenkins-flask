import configparser
import os
import sys

# Get the absolute path to the alembic.ini file
config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'migrations', 'alembic.ini')

print(f"Attempting to read config from: {config_path}")

config = configparser.ConfigParser()
try:
    read_files = config.read(config_path)
    if not read_files:
        print(f"ERROR: Could not read {config_path}. File might be empty or inaccessible.")
        sys.exit(1)

    print(f"Successfully read config file(s): {read_files}")

    if 'alembic' not in config:
        print("ERROR: [alembic] section not found in config.")
        sys.exit(1)

    script_location = config['alembic'].get('script_location')
    if script_location is None:
        print("ERROR: 'script_location' key not found in [alembic] section.")
        sys.exit(1)

    print(f"Success! 'script_location' found: {script_location}")

except configparser.Error as e:
    print(f"CONFIGPARSER ERROR: Failed to parse alembic.ini: {e}")
    sys.exit(1)
except Exception as e:
    print(f"UNEXPECTED ERROR: {e}")
    sys.exit(1)
