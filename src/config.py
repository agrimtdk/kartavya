import os

# Project root directory resolution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = "kartavya"
APP_SUBTITLE = "Personal Productivity Workspace"

DEFAULT_TAGLINE = "Make today count. Own your time."

# Environment & Deployment Modes (Phase 8)
# Modes: "local" (desktop default with JSON file persistence),
#        "web_demo" (in-memory per session state, no disk persistence),
#        "web_single_user" (single user with persistent disk volume)
KARTAVYA_ENV = os.getenv("KARTAVYA_ENV", "development").lower()
KARTAVYA_MODE = os.getenv("KARTAVYA_MODE", "local").lower()

# Absolute paths based on PROJECT_ROOT or environment overrides
KARTAVYA_DATA_DIR = os.getenv("KARTAVYA_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
QUOTE_API_TIMEOUT = float(os.getenv("KARTAVYA_QUOTE_API_TIMEOUT", "3.0"))

# Navigation item labels
NAV_ITEMS = [
    {"label": "Dashboard & Timeline", "icon": "⚡", "active": True},
    {"label": "Profiles (Phase 3)", "icon": "📁", "active": False},
    {"label": "Analytics (Phase 4)", "icon": "📊", "active": False},
    {"label": "Settings", "icon": "⚙️", "active": False},
]

# Color Tokens - Light Theme
LIGHT_THEME = {
    "bg": "#FFFDF6",
    "surface": "#FFFFFF",
    "surface_alt": "#F4F0EA",
    "text": "#000000",
    "text_muted": "#4A4A4A",
    "border": "#000000",
    "shadow": "#000000",
    "primary": "#FFE600",    # Yellow
    "secondary": "#00E5FF",  # Cyan
    "highlight": "#FF5277",  # Coral / Pink
    "success": "#00E676",    # Lime Green
    "card_bg": "#FFFFFF",
}

# Color Tokens - Dark Theme (Night Mode)
DARK_THEME = {
    "bg": "#121212",
    "surface": "#27272A",
    "surface_alt": "#18181B",
    "text": "#F4F4F5",
    "text_muted": "#A1A1AA",
    "border": "#000000",
    "shadow": "#000000",
    "primary": "#FACC15",    # Neon Yellow
    "secondary": "#FF4081",  # Neon Pink
    "highlight": "#2DD4BF",  # Turquoise
    "violet": "#C084FC",     # Violet
    "success": "#00E676",
    "card_bg": "#27272A",
}

# Neo-Brutalist Layout Metrics
BORDER_WIDTH = "3px"
SHADOW_OFFSET = "5px"
BORDER_RADIUS = "2px"

# Task Health Classification Thresholds (Phase 5)
HEALTH_STRONG_THRESHOLD = 80          # >= 80% completion
HEALTH_STABLE_THRESHOLD = 60          # >= 60% and < 80%
HEALTH_NEEDS_ATTENTION_THRESHOLD = 1  # > 0% and < 60% (0% is INACTIVE)

# Schema Version & Task Priorities (Phase 6)
SCHEMA_VERSION = 4
PRIORITY_LOW = "Low"
PRIORITY_MEDIUM = "Medium"
PRIORITY_HIGH = "High"
PRIORITY_CHOICES = ["Low", "Medium", "High"]

DEFAULT_DAILY_TARGET_PCT = 80.0

# Input Validation Bounds & Backup Settings (Phase 7)
MAX_WORKSPACE_NAME_LEN = 30
MAX_TASK_NAME_LEN = 40
MAX_TITLE_LEN = 60

MAX_BACKUPS_COUNT = 5
BACKUP_DIR = os.path.join(KARTAVYA_DATA_DIR, "backups")

