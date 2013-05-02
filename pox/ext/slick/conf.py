# This file should have the configuration for the slick controller.

# Application configuration referesh rate in seconds.
APPCONF_REFRESH_RATE = 1


# Number of function instances per machine.
# This number should be specific to each Middlebox hardware. But for now we keep a global limit.
# This number should be learned for each middlebox.
MAX_FUNCTION_INSTANCES = 10


# Middlebox Settings
# Username and Password for the Middleboxes
MB_USERNAME = "openflow"
MB_PASSWORD = "openflow"
# Default location to download code if the location by the user is not provided.
DEFAULT_CODE_LOCATION = "/tmp/"
