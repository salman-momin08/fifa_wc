"""
Application-wide Constants.

Eliminates magic numbers and hardcoded string literals across the codebase.
All threshold values, defaults, and named configuration values are centralized here.
"""

# ── Crowd Density Thresholds (%) ──────────────────────────────────────────────
DENSITY_THRESHOLD_LOW: int = 50
DENSITY_THRESHOLD_HIGH: int = 80
DENSITY_CRITICAL: int = 90

# Aliases used by analytics.py for semantic clarity
CROWD_HIGH_DENSITY_THRESHOLD: int = DENSITY_THRESHOLD_HIGH
CROWD_MODERATE_DENSITY_THRESHOLD: int = DENSITY_THRESHOLD_LOW
CROWD_CRITICAL_FORECAST_THRESHOLD: int = DENSITY_CRITICAL

# ── Match Telemetry Defaults ──────────────────────────────────────────────────
DEFAULT_HOME_TEAM: str = "CANADA"
DEFAULT_HOME_FLAG: str = "🇨🇦"
DEFAULT_AWAY_TEAM: str = "USA"
DEFAULT_AWAY_FLAG: str = "🇺🇸"
DEFAULT_MATCH_MINUTE: str = "76'"
DEFAULT_STADIUM_ATTENDANCE: str = "68,243"
DEFAULT_CAPACITY_PCT: float = 92.4

# Match simulation timing constants
MATCH_CYCLE_SECONDS: int = 5400          # Full 90-minute match cycle in seconds
MATCH_SEED_INTERVAL_SECONDS: int = 5     # Client polling interval for live data
POSSESSION_BASE_HOME: int = 52           # Default home possession %
DEFAULT_SHOTS_HOME: int = 12
DEFAULT_SHOTS_AWAY: int = 9
DEFAULT_PASS_ACCURACY_HOME: int = 85
DEFAULT_PASS_ACCURACY_AWAY: int = 81

# ── Sustainability Impact Metrics ─────────────────────────────────────────────
PLASTIC_SAVED_PER_REFILL_GRAMS: float = 25.0       # Grams of plastic per refill
CO2_REDUCED_PER_TRANSIT_TRIP_KG: float = 2.6       # kg CO2 per public transit trip
CO2_REDUCED_PER_BOTTLE_KG: float = 0.08            # kg CO2 per plastic bottle avoided
GREEN_SCORE_PER_REFILL: int = 10                   # Green score points per refill
GREEN_SCORE_PER_TRANSIT: int = 100                 # Green score points per transit trip
# Legacy alias for existing code
CO2_REDUCED_PER_TRANSIT_TRIP_GRAMS: int = 1200

# ── API / LLM Configuration ───────────────────────────────────────────────────
LLM_REQUEST_TIMEOUT_SECONDS: float = 10.0          # httpx timeout for Gemini API
LLM_CONFIDENCE_THRESHOLD: float = 0.60             # Minimum confidence before fallback
RATE_LIMIT_WINDOW_SECONDS: int = 60
RATE_LIMIT_MAX_REQUESTS: int = 60

# ── User Roles ────────────────────────────────────────────────────────────────
ROLE_FAN: str = "fan"
ROLE_VOLUNTEER: str = "volunteer"
ROLE_ORGANIZER: str = "organizer"
ROLE_ADMIN: str = "admin"

# ── Incident Lifecycle Statuses ───────────────────────────────────────────────
INCIDENT_STATUS_DRAFT: str = "draft"
INCIDENT_STATUS_ACTIVE: str = "active"
INCIDENT_STATUS_RESOLVED: str = "resolved"

# ── WebSocket Configuration ───────────────────────────────────────────────────
WS_RECONNECT_MAX_ATTEMPTS: int = 5
WS_RECONNECT_MAX_DELAY_SECONDS: int = 30
