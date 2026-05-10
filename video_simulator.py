"""
Video frame simulation module with realistic security scenarios
"""
import random
from typing import Dict, List
from datetime import datetime


class VideoFrameSimulator:
    """Simulates realistic video frames with security scenarios"""
    
    def __init__(self):
        self.vehicle_database = {
            "Blue Ford F150": {"type": "pickup truck", "color": "blue", "make": "Ford", "model": "F150"},
            "Red Toyota Camry": {"type": "sedan", "color": "red", "make": "Toyota", "model": "Camry"},
            "Black Honda Civic": {"type": "sedan", "color": "black", "make": "Honda", "model": "Civic"},
            "White Chevrolet Silverado": {"type": "pickup truck", "color": "white", "make": "Chevrolet", "model": "Silverado"},
            "Gray Nissan Altima": {"type": "sedan", "color": "gray", "make": "Nissan", "model": "Altima"}
        }
        
        self.recurring_vehicles = {}  # Track vehicle appearances
        self.person_ids = {}  # Track person movements
        
        self.scenarios = self._create_scenario_templates()
    
    def _create_scenario_templates(self) -> List[Dict]:
        """Create realistic security scenario templates"""
        return [
            # Normal scenarios
            {"weight": 30, "template": "{vehicle} parked at {location}", "type": "normal"},
            {"weight": 25, "template": "Person walking near {location}", "type": "normal"},
            {"weight": 20, "template": "{vehicle} driving past {location}", "type": "normal"},
            {"weight": 15, "template": "Two people talking at {location}", "type": "normal"},
            
            # Suspicious scenarios
            {"weight": 3, "template": "Person loitering near {location}", "type": "suspicious"},
            {"weight": 2, "template": "Unidentified person approaching {location}", "type": "suspicious"},
            {"weight": 2, "template": "{vehicle} circling {location} slowly", "type": "suspicious"},
            {"weight": 1, "template": "Person running near {location}", "type": "suspicious"},
            {"weight": 1, "template": "Group of people gathering at {location}", "type": "suspicious"},
            {"weight": 1, "template": "Person carrying large bag near {location}", "type": "suspicious"},
        ]
    
    def generate_frame_description(self, frame_number: int, telemetry: Dict) -> Dict:
        """Generate realistic frame description based on time and location"""
        timestamp = datetime.strptime(telemetry["timestamp"], "%Y-%m-%d %H:%M:%S")
        hour = timestamp.hour
        location = telemetry["location"]
        
        # Select scenario based on weights
        scenario = random.choices(
            self.scenarios,
            weights=[s["weight"] for s in self.scenarios]
        )[0]
        
        # Generate description
        if "{vehicle}" in scenario["template"]:
            vehicle = random.choice(list(self.vehicle_database.keys()))
            description = scenario["template"].format(vehicle=vehicle, location=location)
            
            # Track recurring vehicles
            if vehicle not in self.recurring_vehicles:
                self.recurring_vehicles[vehicle] = []
            self.recurring_vehicles[vehicle].append({
                "frame": frame_number,
                "timestamp": telemetry["timestamp"],
                "location": location
            })
            
            objects = [{
                "type": "vehicle",
                "details": self.vehicle_database[vehicle],
                "identifier": vehicle,
                "location": location,
                "confidence": round(random.uniform(0.85, 0.99), 2)
            }]
        else:
            description = scenario["template"].format(location=location)
            objects = [{
                "type": "person",
                "details": {"activity": scenario["template"].split()[0]},
                "location": location,
                "confidence": round(random.uniform(0.80, 0.95), 2)
            }]
        
        # Add time-based context
        if 22 <= hour or hour < 6:
            if scenario["type"] == "normal":
                description += " (night time)"
            else:
                description += " (unusual for this hour)"
        
        # Occasionally add empty frames
        if random.random() < 0.1:
            description = f"No activity detected at {location}"
            objects = []
        
        return {
            "description": description,
            "objects": objects,
            "scenario_type": scenario["type"],
            "conditions": self._get_environmental_conditions(hour)
        }
    
    def _get_environmental_conditions(self, hour: int) -> Dict:
        """Add environmental context"""
        conditions = {
            "visibility": "good",
            "lighting": "daylight"
        }
        
        if 6 <= hour < 8:
            conditions["lighting"] = "dawn"
        elif 18 <= hour < 20:
            conditions["lighting"] = "dusk"
        elif 20 <= hour or hour < 6:
            conditions["lighting"] = "night"
            if random.random() < 0.3:
                conditions["visibility"] = "poor"
        
        return conditions
    
    def get_recurring_vehicles(self) -> Dict:
        """Get vehicles that appeared multiple times"""
        return {
            vehicle: appearances
            for vehicle, appearances in self.recurring_vehicles.items()
            if len(appearances) >= 2
        }