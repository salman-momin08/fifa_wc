"""
Application Constants.
Eliminates magic numbers and hardcoded string literals across the codebase.
"""

# Crowd Density Thresholds (%)
DENSITY_THRESHOLD_LOW = 50
DENSITY_THRESHOLD_HIGH = 80
DENSITY_CRITICAL = 90

# Match Telemetry Defaults
DEFAULT_HOME_TEAM = "CANADA"
DEFAULT_HOME_FLAG = "🇨🇦"
DEFAULT_AWAY_TEAM = "USA"
DEFAULT_AWAY_FLAG = "🇺🇸"
DEFAULT_MATCH_MINUTE = "76'"
DEFAULT_STADIUM_ATTENDANCE = "68,243"
DEFAULT_CAPACITY_PCT = 92.4

# Sustainability Metrics
PLASTIC_SAVED_PER_REFILL_GRAMS = 25
CO2_REDUCED_PER_TRANSIT_TRIP_GRAMS = 1200

# User Roles
ROLE_FAN = "fan"
ROLE_VOLUNTEER = "volunteer"
ROLE_ORGANIZER = "organizer"
ROLE_ADMIN = "admin"

# Incident Statuses
INCIDENT_STATUS_DRAFT = "draft"
INCIDENT_STATUS_ACTIVE = "active"
INCIDENT_STATUS_RESOLVED = "resolved"
