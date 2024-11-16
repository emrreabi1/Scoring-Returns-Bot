import logging
from datetime import datetime
from configs.config import LOGGING_PATH

def configure_logging(team_name, author_id):
    """
    Creates and configures a logger for a specific team, with log files named after the team.

    Parameters:
    - The name of the team to include in the log file name.

    Returns:
    - A logger instance configured for the team.
    """
    logger = logging.getLogger(team_name)
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Clear existing handlers

    author_id = str(author_id)

    # Create logging directory if it doesn't exist
    LOGGING_PATH.mkdir(parents=True, exist_ok=True)

    # Create handlers
    file_handler = logging.FileHandler(str(LOGGING_PATH / f"{author_id}{team_name}.log"))
    console_handler = logging.StreamHandler()

    # Create a logging format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def calculate_time_remaining(date_time_str):
    # Parsing the given date-time string and removing timezone information
    target_date = datetime.fromisoformat(date_time_str)
    if target_date.tzinfo is not None:
        target_date = target_date.replace(tzinfo=None)

    # Getting the current date and time (as offset-naive)
    current_date = datetime.now()

    # Calculating the time difference
    time_difference = target_date - current_date

    # Extracting days, hours, minutes, and seconds
    days = time_difference.days
    seconds = time_difference.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return days, hours, minutes, seconds