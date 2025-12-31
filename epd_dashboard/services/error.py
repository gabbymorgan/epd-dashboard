import os
from datetime import datetime, timezone

def init_error_file():
    if not os.path.exists("./errors.log"):
        os.mknod("./errors.log")

def log_error(error_message: str):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "errors.log"), 'r') as error_log:
        error_log_entry = str(error_message) + str(datetime.now(timezone.utc))
        error_log.write(error_log_entry)