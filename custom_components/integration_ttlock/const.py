"""Constants for integration_ttlock."""
# Base component constants
NAME = "TTLock Integration"
DOMAIN = "integration_ttlock"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/nikolai5slo/integration_ttlock/issues"

# Icons
ICON = "mdi:format-quote-close"

# Platforms
LOCK = "lock"
SENSOR = "sensor"
PLATFORMS = [SENSOR, LOCK]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_SERVER = "server"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_USERNAME = "username"
CONF_REFRESH_TOKEN = "refresh_token"

# Input value
INPUT_PASSWORD = "password"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
