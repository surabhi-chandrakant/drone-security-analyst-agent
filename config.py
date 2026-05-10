"""
Configuration file for Drone Security Analyst Agent
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
DB_DIR = BASE_DIR / "database"

# Create directories if they don't exist
for dir_path in [DATA_DIR, LOGS_DIR, OUTPUT_DIR, DB_DIR]:
    dir_path.mkdir(exist_ok=True)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# Database Configuration
DATABASE_PATH = DB_DIR / "drone_security.db"

# Alert Rules Configuration
ALERT_RULES = {
    "loitering": {
        "time_threshold": 300,  # 5 minutes in seconds
        "description": "Person detected in same area for extended period"
    },
    "midnight_activity": {
        "start_hour": 22,  # 10 PM
        "end_hour": 6,     # 6 AM
        "description": "Activity detected during restricted hours"
    },
    "restricted_zone": {
        "zones": ["main_gate", "warehouse", "parking_lot"],
        "description": "Unauthorized access to restricted zone"
    },
    "vehicle_repeat": {
        "threshold": 2,  # Alert if same vehicle appears this many times
        "description": "Same vehicle detected multiple times"
    },
    "suspicious_behavior": {
        "keywords": ["running", "climbing", "jumping fence", "breaking"],
        "description": "Suspicious activity detected"
    }
}

# Telemetry Configuration
TELEMETRY_UPDATE_INTERVAL = 1  # seconds
DRONE_SPECS = {
    "altitude_range": (10, 50),  # meters
    "coverage_radius": 100,      # meters
    "camera_fov": 90            # degrees
}

# Object Detection Configuration
DETECTION_CONFIDENCE_THRESHOLD = 0.7
SUPPORTED_OBJECTS = [
    "person", "car", "truck", "bicycle", "motorcycle",
    "bus", "van", "suv", "pickup truck", "sedan"
]

# Gemini Model Configuration
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 1024