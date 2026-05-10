"""
Telemetry simulation module for drone data generation
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List
import config


class TelemetrySimulator:
    """Simulates realistic drone telemetry data"""
    
    def __init__(self):
        self.current_time = datetime.now()
        self.current_position = {"lat": 19.0, "lon": 73.0}  # Nashik coordinates
        self.current_altitude = 30.0
        self.locations = [
            "main_gate", "parking_lot", "warehouse", "garden",
            "north_perimeter", "south_perimeter", "garage", "entrance"
        ]
    
    def generate_telemetry(self, frame_number: int) -> Dict:
        """Generate telemetry data for a specific frame"""
        # Increment time
        self.current_time += timedelta(seconds=config.TELEMETRY_UPDATE_INTERVAL)
        
        # Simulate slight position changes (drone hovering/patrolling)
        self.current_position["lat"] += random.uniform(-0.0001, 0.0001)
        self.current_position["lon"] += random.uniform(-0.0001, 0.0001)
        
        # Altitude variation
        self.current_altitude += random.uniform(-2, 2)
        self.current_altitude = max(
            config.DRONE_SPECS["altitude_range"][0],
            min(self.current_altitude, config.DRONE_SPECS["altitude_range"][1])
        )
        
        telemetry = {
            "timestamp": self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "frame_number": frame_number,
            "position": {
                "latitude": round(self.current_position["lat"], 6),
                "longitude": round(self.current_position["lon"], 6)
            },
            "altitude": round(self.current_altitude, 2),
            "battery_level": max(20, 100 - (frame_number * 0.1)),
            "signal_strength": random.randint(70, 100),
            "location": random.choice(self.locations),
            "camera_angle": random.randint(-45, 45),
            "wind_speed": round(random.uniform(0, 10), 1)
        }
        
        return telemetry
    
    def reset(self):
        """Reset simulator to initial state"""
        self.current_time = datetime.now()
        self.current_position = {"lat": 19.0, "lon": 73.0}
        self.current_altitude = 30.0