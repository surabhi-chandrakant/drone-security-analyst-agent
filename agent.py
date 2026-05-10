"""
Main Drone Security Analyst Agent
Orchestrates all components for real-time security monitoring
"""
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

import config
from database import FrameIndexer
from telemetry import TelemetrySimulator
from video_simulator import VideoFrameSimulator
from ai_analyzer import AIAnalyzer
from alert_system import AlertSystem


class DroneSecurityAgent:
    """Main agent that coordinates security analysis"""
    
    def __init__(self, api_key: str = None):
        print("🚁 Initializing Drone Security Analyst Agent...")
        
        # Initialize components
        self.db = FrameIndexer()
        self.telemetry_sim = TelemetrySimulator()
        self.video_sim = VideoFrameSimulator()
        self.ai_analyzer = AIAnalyzer(api_key)
        self.alert_system = AlertSystem()
        
        # Storage for processed data
        self.processed_frames = []
        self.all_alerts = []
        
        print("✅ Agent initialized successfully")
    
    def process_frame(self, frame_number: int) -> Dict:
        """Process a single video frame with telemetry"""
        # Generate telemetry
        telemetry = self.telemetry_sim.generate_telemetry(frame_number)
        
        # Generate video frame description
        frame_sim = self.video_sim.generate_frame_description(frame_number, telemetry)
        
        # Prepare frame data
        frame_data = {
            "frame_number": frame_number,
            "timestamp": telemetry["timestamp"],
            "description": frame_sim["description"],
            "objects": frame_sim["objects"],
            "telemetry": telemetry,
            "location": telemetry["location"]
        }
        
        # AI Analysis
        ai_analysis = self.ai_analyzer.analyze_frame(
            frame_sim["description"],
            telemetry
        )
        
        # Store frame in database
        frame_id = self.db.insert_frame(frame_data)
        frame_data["frame_id"] = frame_id
        
        # Store detected objects
        for obj in frame_sim["objects"]:
            obj["timestamp"] = telemetry["timestamp"]
            self.db.insert_object(frame_id, obj)
        
        # Evaluate for alerts
        alerts = self.alert_system.evaluate_frame(frame_data, ai_analysis)
        
        # Store alerts
        for alert in alerts:
            alert["frame_id"] = frame_id
            alert_id = self.db.insert_alert(alert)
            alert["alert_id"] = alert_id
            self.all_alerts.append(alert)
        
        # Combine all data
        result = {
            **frame_data,
            "ai_analysis": ai_analysis,
            "alerts": alerts
        }
        
        self.processed_frames.append(result)
        return result
    
    def run_monitoring_session(self, num_frames: int = 50, verbose: bool = True):
        """Run a complete monitoring session"""
        print(f"\n{'='*70}")
        print(f"🎥 Starting Drone Security Monitoring Session")
        print(f"{'='*70}\n")
        print(f"Processing {num_frames} frames...\n")
        
        for i in range(num_frames):
            frame_result = self.process_frame(i + 1)
            
            if verbose:
                self._print_frame_summary(frame_result)
            
            # Print alerts immediately
            for alert in frame_result["alerts"]:
                print(f"\n{self.alert_system.format_alert(alert)}")
        
        print(f"\n{'='*70}")
        print(f"✅ Monitoring Session Completed")
        print(f"{'='*70}\n")
        
        self._print_session_summary()
    
    def _print_frame_summary(self, frame: Dict):
        """Print formatted frame information"""
        print(f"Frame {frame['frame_number']:03d} | {frame['timestamp']} | {frame['location']}")
        print(f"  📹 {frame['description']}")
        
        if frame['objects']:
            print(f"  🎯 Objects: {', '.join([obj['type'] for obj in frame['objects']])}")
        
        ai = frame.get('ai_analysis', {})
        if ai.get('security_level'):
            print(f"  🔍 Security Level: {ai['security_level']}")
    
    def _print_session_summary(self):
        """Print summary of the monitoring session"""
        print("📊 Session Summary:")
        print(f"  • Total Frames Processed: {len(self.processed_frames)}")
        print(f"  • Total Alerts Generated: {len(self.all_alerts)}")
        
        # Alert breakdown
        alert_types = {}
        for alert in self.all_alerts:
            alert_type = alert['alert_type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        if alert_types:
            print(f"\n  Alert Breakdown:")
            for alert_type, count in alert_types.items():
                print(f"    - {alert_type}: {count}")
        
        # Recurring vehicles
        recurring = self.video_sim.get_recurring_vehicles()
        if recurring:
            print(f"\n  🚗 Recurring Vehicles:")
            for vehicle, appearances in recurring.items():
                print(f"    - {vehicle}: {len(appearances)} times")
        
        # Database stats
        db_stats = self.db.get_statistics()
        print(f"\n  💾 Database Statistics:")
        print(f"    - Total Objects Tracked: {db_stats['total_objects']}")
        print(f"    - Unique Object Types: {len(db_stats['top_objects'])}")
    
    def query_system(self, query: str) -> str:
        """Answer questions about the surveillance data"""
        print(f"\n❓ Query: {query}")
        
        # Try database queries first
        if "truck" in query.lower() or "vehicle" in query.lower():
            results = self.db.query_frames_by_object("truck")
            if results:
                response = f"Found {len(results)} frames with trucks:\n"
                for r in results[:3]:
                    response += f"  - {r['timestamp']}: {r['description']}\n"
                print(f"💡 Answer:\n{response}")
                return response
        
        # Use AI for complex queries
        response = self.ai_analyzer.answer_query(query, self.processed_frames[-10:])
        print(f"💡 Answer: {response}")
        return response
    
    def generate_video_summary(self) -> str:
        """Generate summary of entire video session"""
        print("\n📝 Generating Video Summary...")
        summary = self.ai_analyzer.summarize_video_session(self.processed_frames)
        print(f"\n{summary}\n")
        return summary
    
    def export_results(self, output_dir: Path = config.OUTPUT_DIR):
        """Export all results to JSON files"""
        print("\n💾 Exporting Results...")
        
        # Export frames
        frames_file = output_dir / "processed_frames.json"
        with open(frames_file, 'w') as f:
            json.dump(self.processed_frames, f, indent=2, default=str)
        print(f"  ✓ Frames: {frames_file}")
        
        # Export alerts
        alerts_file = output_dir / "alerts.json"
        with open(alerts_file, 'w') as f:
            json.dump(self.all_alerts, f, indent=2, default=str)
        print(f"  ✓ Alerts: {alerts_file}")
        
        # Export recurring vehicles
        recurring_file = output_dir / "recurring_vehicles.json"
        with open(recurring_file, 'w') as f:
            json.dump(self.video_sim.get_recurring_vehicles(), f, indent=2, default=str)
        print(f"  ✓ Recurring Vehicles: {recurring_file}")
        
        # Export database stats
        stats_file = output_dir / "statistics.json"
        stats = {
            "database": self.db.get_statistics(),
            "alerts": self.alert_system.get_alert_statistics(),
            "session": {
                "total_frames": len(self.processed_frames),
                "total_alerts": len(self.all_alerts),
                "start_time": self.processed_frames[0]['timestamp'] if self.processed_frames else None,
                "end_time": self.processed_frames[-1]['timestamp'] if self.processed_frames else None
            }
        }
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"  ✓ Statistics: {stats_file}")
        
        print("✅ Export complete!")
    
    def demonstrate_indexing(self):
        """Demonstrate frame-by-frame indexing capabilities"""
        print(f"\n{'='*70}")
        print("🔍 Demonstrating Frame-by-Frame Indexing")
        print(f"{'='*70}\n")
        
        # Query by object type
        print("1. Query frames containing 'truck':")
        truck_frames = self.db.query_frames_by_object("truck")
        for frame in truck_frames[:3]:
            print(f"   Frame {frame['frame_number']}: {frame['description']}")
        
        # Query by time
        if self.processed_frames:
            print("\n2. Query frames in time range:")
            start = self.processed_frames[0]['timestamp']
            end = self.processed_frames[min(10, len(self.processed_frames)-1)]['timestamp']
            time_frames = self.db.query_frames_by_time(start, end)
            print(f"   Found {len(time_frames)} frames between {start} and {end}")
        
        # Search by keyword
        print("\n3. Full-text search for 'loitering':")
        search_results = self.db.search_frames("loitering")
        for frame in search_results[:3]:
            print(f"   Frame {frame['frame_number']}: {frame['description']}")
        
        # Recent alerts
        print("\n4. Recent alerts:")
        recent = self.db.get_recent_alerts(5)
        for alert in recent:
            print(f"   {alert['alert_type']}: {alert['description']}")
        
        print()
    
    def close(self):
        """Clean up resources"""
        self.db.close()
        print("\n👋 Agent shutdown complete")


def main():
    """Main execution function"""
    # Initialize agent (will use API key from environment or config)
    agent = DroneSecurityAgent()
    
    # Run monitoring session
    agent.run_monitoring_session(num_frames=50, verbose=True)
    
    # Demonstrate indexing capabilities
    agent.demonstrate_indexing()
    
    # Generate summary
    agent.generate_video_summary()
    
    # Answer sample queries
    agent.query_system("What vehicles were detected?")
    agent.query_system("Were there any suspicious activities?")
    
    # Export results
    agent.export_results()
    
    # Cleanup
    agent.close()


if __name__ == "__main__":
    main()