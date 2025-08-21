import logging
import sys
from logging.handlers import RotatingFileHandler

# Define the log format and the log file name
LOG_FORMAT = '%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'app.log'

def setup_logging():
    # Get the root logger.
    # All other loggers will inherit its settings.
    root_logger = logging.getLogger()
    
    # Check if handlers have already been added to the root logger.
    # This prevents adding duplicate handlers if this function is called more than once.
    if root_logger.hasHandlers():
        return

    root_logger.setLevel(logging.INFO)

    # --- Create a handler for console output (stdout) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # --- Create a handler for file output ---
    # RotatingFileHandler is important for long-running applications.
    # It prevents the log file from growing indefinitely.
    # `maxBytes=10MB`, `backupCount=5` means it will keep up to 5 old log files of 10MB each.
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Add the handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")