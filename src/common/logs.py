import logging
import json
import time
import os
from datetime import datetime
import inspect
import traceback

# Create the 'logs' directory if it doesn't exist
logs_dir = "/app/logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure the file handler
log_file_name = f"my_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
log_file_path = os.path.join(logs_dir, log_file_name)
file_handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(custom_funcName)s - %(message)s"
)
file_handler.setFormatter(formatter)

# Configure the console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Configure the root logger
logging.basicConfig(handlers=[file_handler, console_handler], level=logging.DEBUG)

# Define a dictionary to store logs in JSON
logs_json = {}

# Function to serialize logs to JSON
def serialize_logs(logs_json, filename="logs_container.json"):
    full_path = os.path.join(logs_dir, filename)
    with open(full_path, "w") as f:
        json.dump(logs_json, f, indent=4)

# Create a function to log messages with additional information
def log_message(message, level="INFO", extra_data={}, func=None):
    """
    Logs a message with additional information.
    If 'func' is provided, it is used as the function name.
    If not, it is detected automatically.
    """
    # Get information about the caller
    caller_frame = inspect.currentframe().f_back
    caller_line = caller_frame.f_lineno

    if func is None:
        caller_method = caller_frame.f_code.co_name
    else:
        caller_method = func.__name__ if callable(func) else str(func)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": f"{message} Error: {traceback.format_exc()}",
        "extra_data": extra_data,
        "method": caller_method,
        "line": caller_line,
    }
    logs_json[time.time()] = log_entry

    # Add the method name and line number to the extra_data dictionary
    extra_data["custom_funcName"] = caller_method
    extra_data["line"] = caller_line

    logger = logging.getLogger(__name__)
    logger.log(logging.getLevelName(level), message, extra=extra_data)
    # serialize_logs(logs_json)

if __name__ == "__main__":
    # Example usage
    log_message("This is an informational message from the main level.")

    # Serialize logs to JSON every certain interval
    while True:
        serialize_logs(logs_json)
        time.sleep(30)  # Serialize every 30 seconds
