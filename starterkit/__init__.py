"""
This module sets up a logger for the package with a console handler and formatter.
The logger's level is set to INFO, and the console handler's level is set to DEBUG.
"""

import logging

# Create a logger for the package
logger = logging.getLogger(__package__)
logger.setLevel(logging.WARNING)

# Create a console handler to write logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Create a formatter and set it for the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
