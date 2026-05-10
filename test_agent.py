"""
Test Suite for Drone Security Analyst Agent
Validates all functionality as per assignment requirements
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import FrameIndexer
from telemetry import TelemetrySimulator
from video_simulator import VideoFrameSimulator
from alert_system import AlertSystem
from agent import DroneSecurityAgent
import config


class TestTelemetrySimulator(unittest.TestCase):
    """Test telemetry data generation"""
    
    def setUp(self):
        self.sim = TelemetrySimulator()
    
    def test_telemetry_generation(self):
        """Test that telemetry data is generated correctly"""
        telemetry = self.sim.generate_telemetry(1)
        
        self.assertIn('timestamp', telemetry)
        self.assertIn('position', telemetry)
        self.assertIn('altitude', telemetry)
        self.assertIn('location', telemetry)
        
        # Check altitude is within range
        self.assertGreaterEqual(telemetry['altitude'], config.DRONE_SPECS['altitude_range'][0])
        self.assertLessEqual(telemetry['altitude'], config.DRONE_SPECS['altitude_range'][1])
    
    def test_sequential_frames(self):
        """Test that sequential frames have increasing timestamps"""
        t1 = self.sim.generate_telemetry(1)
        t2 = self.sim.generate_telemetry(2)
        
        time1 = datetime.strptime(t1['timestamp'], "%Y-%m-%d %H:%M:%S")
        time2 = datetime.strptime(t2['timestamp'], "%Y-%m-%d %H:%M:%S")
        
        self.assertGreater(time2, time1)


class TestVideoFrameSimulator(unittest.TestCase):
    """Test video frame simulation"""
    
    def setUp(self):
        self.sim = VideoFrameSimulator()
        self.telemetry_sim = TelemetrySimulator()
    
    def test_frame_description_generation(self):
        """Test that frame descriptions are generated"""
        telemetry = self.telemetry_sim.generate_telemetry(1)
        frame = self.sim.generate_frame_description(1, telemetry)
        
        self.assertIn('description', frame)
        self.assertIn('objects', frame)
        self.assertIsInstance(frame['objects'], list)
    
    def test_object_detection(self):
        """Test that objects are detected in frames"""
        telemetry = self.telemetry_sim.generate_telemetry(1)
        
        # Generate multiple frames to get objects
        found_vehicle = False
        found_person = False
        
        for i in range(20):
            frame = self.sim.generate_frame_description(i, telemetry)
            for obj in frame['objects']:
                if obj['type'] == 'vehicle':
                    found_vehicle = True
                if obj['type'] == 'person':
                    found_person = True
        
        # At least one type should be found in 20 frames
        self.assertTrue(found_vehicle or found_person)
    
    def test_recurring_vehicle_tracking(self):
        """Test that recurring vehicles are tracked"""
        telemetry = self.telemetry_sim.generate_telemetry(1)
        
        # Generate enough frames to potentially have recurring vehicles
        for i in range(30):
            self.sim.generate_frame_description(i, telemetry)
        
        recurring = self.sim.get_recurring_vehicles()
        # Should track vehicles even if none recurred yet
        self.assertIsInstance(recurring, dict)


class TestFrameIndexer(unittest.TestCase):
    """Test database indexing functionality"""
    
    def setUp(self):
        # Use temporary database for testing
        self.db_path = Path("test_security.db")
        if self.db_path.exists():
            self.db_path.unlink()
        self.db = FrameIndexer(self.db_path)
    
    def tearDown(self):
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_frame_insertion(self):
        """Test inserting frames into database"""
        frame_data = {
            'timestamp': '2024-01-01 12:00:00',
            'frame_number': 1,
            'telemetry': {'altitude': 30, 'location': 'gate'},
            'description': 'Blue truck at gate',
            'objects': [{'type': 'vehicle', 'identifier': 'Blue Ford F150'}]
        }
        
        frame_id = self.db.insert_frame(frame_data)
        self.assertIsInstance(frame_id, int)
        self.assertGreater(frame_id, 0)
    
    def test_object_insertion(self):
        """Test inserting objects into database"""
        frame_data = {
            'timestamp': '2024-01-01 12:00:00',
            'frame_number': 1,
            'telemetry': {'altitude': 30, 'location': 'gate'},
            'description': 'Blue truck at gate',
            'objects': []
        }
        frame_id = self.db.insert_frame(frame_data)
        
        obj_data = {
            'type': 'vehicle',
            'details': {'color': 'blue', 'model': 'F150'},
            'timestamp': '2024-01-01 12:00:00',
            'location': 'gate'
        }
        obj_id = self.db.insert_object(frame_id, obj_data)
        
        self.assertIsInstance(obj_id, int)
        self.assertGreater(obj_id, 0)
    
    def test_query_by_object_type(self):
        """Test querying frames by object type"""
        # Insert test data
        frame_data = {
            'timestamp': '2024-01-01 12:00:00',
            'frame_number': 1,
            'telemetry': {'altitude': 30, 'location': 'gate'},
            'description': 'Blue truck at gate',
            'objects': []
        }
        frame_id = self.db.insert_frame(frame_data)
        
        obj_data = {
            'type': 'truck',
            'details': {},
            'timestamp': '2024-01-01 12:00:00',
            'location': 'gate'
        }
        self.db.insert_object(frame_id, obj_data)
        
        # Query
        results = self.db.query_frames_by_object('truck')
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['frame_number'], 1)
    
    def test_alert_insertion(self):
        """Test inserting alerts"""
        frame_data = {
            'timestamp': '2024-01-01 00:00:00',
            'frame_number': 1,
            'telemetry': {'altitude': 30, 'location': 'gate'},
            'description': 'Person at gate',
            'objects': []
        }
        frame_id = self.db.insert_frame(frame_data)
        
        alert_data = {
            'frame_id': frame_id,
            'alert_type': 'midnight_activity',
            'severity': 'high',
            'description': 'Activity at midnight',
            'timestamp': '2024-01-01 00:00:00'
        }
        alert_id = self.db.insert_alert(alert_data)
        
        self.assertIsInstance(alert_id, int)
        self.assertGreater(alert_id, 0)
    
    def test_statistics(self):
        """Test database statistics generation"""
        stats = self.db.get_statistics()
        
        self.assertIn('total_frames', stats)
        self.assertIn('total_objects', stats)
        self.assertIn('total_alerts', stats)


class TestAlertSystem(unittest.TestCase):
    """Test alert generation system"""
    
    def setUp(self):
        self.alert_system = AlertSystem()
    
    def test_midnight_activity_detection(self):
        """Test midnight activity alert generation"""
        frame_data = {
            'timestamp': '2024-01-01 00:30:00',
            'description': 'Person walking',
            'location': 'gate',
            'objects': []
        }
        
        ai_analysis = {'security_level': 'low'}
        alerts = self.alert_system.evaluate_frame(frame_data, ai_analysis)
        
        # Should trigger midnight activity alert
        alert_types = [a['alert_type'] for a in alerts]
        self.assertIn('midnight_activity', alert_types)
    
    def test_suspicious_behavior_detection(self):
        """Test suspicious behavior detection"""
        frame_data = {
            'timestamp': '2024-01-01 12:00:00',
            'description': 'Person running near gate',
            'location': 'gate',
            'objects': []
        }
        
        ai_analysis = {'security_level': 'low'}
        alerts = self.alert_system.evaluate_frame(frame_data, ai_analysis)
        
        # Should trigger suspicious behavior alert
        alert_types = [a['alert_type'] for a in alerts]
        self.assertIn('suspicious_behavior', alert_types)
    
    def test_vehicle_repetition_tracking(self):
        """Test that repeated vehicles trigger alerts"""
        vehicle_obj = {
            'type': 'vehicle',
            'identifier': 'Blue Ford F150',
            'details': {'model': 'F150'}
        }
        
        # First appearance
        frame1 = {
            'timestamp': '2024-01-01 10:00:00',
            'description': 'Blue Ford F150 at gate',
            'location': 'gate',
            'objects': [vehicle_obj]
        }
        alerts1 = self.alert_system.evaluate_frame(frame1, {'security_level': 'low'})
        
        # Second appearance - should trigger alert
        frame2 = {
            'timestamp': '2024-01-01 14:00:00',
            'description': 'Blue Ford F150 at garage',
            'location': 'garage',
            'objects': [vehicle_obj]
        }
        alerts2 = self.alert_system.evaluate_frame(frame2, {'security_level': 'low'})
        
        # Check if vehicle repeat alert was generated
        all_alert_types = [a['alert_type'] for a in alerts1 + alerts2]
        self.assertIn('vehicle_repeat', all_alert_types)
    
    def test_alert_formatting(self):
        """Test alert message formatting"""
        alert = {
            'alert_type': 'test',
            'severity': 'high',
            'description': 'Test alert',
            'timestamp': '2024-01-01 12:00:00'
        }
        
        formatted = self.alert_system.format_alert(alert)
        self.assertIn('HIGH', formatted)
        self.assertIn('Test alert', formatted)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete agent"""
    
    def setUp(self):
        # Note: These tests won't use actual Gemini API
        # They test the overall flow with mock/fallback responses
        self.agent = None
    
    def test_agent_initialization(self):
        """Test that agent initializes without errors"""
        try:
            agent = DroneSecurityAgent()
            self.assertIsNotNone(agent)
            agent.close()
        except Exception as e:
            self.fail(f"Agent initialization failed: {e}")
    
    def test_frame_processing(self):
        """Test processing a single frame"""
        agent = DroneSecurityAgent()
        
        result = agent.process_frame(1)
        
        self.assertIn('frame_number', result)
        self.assertIn('description', result)
        self.assertIn('telemetry', result)
        self.assertIn('alerts', result)
        
        agent.close()
    
    def test_export_functionality(self):
        """Test that results export without errors"""
        agent = DroneSecurityAgent()
        agent.process_frame(1)
        
        try:
            agent.export_results()
            
            # Check files were created
            self.assertTrue((config.OUTPUT_DIR / "processed_frames.json").exists())
            self.assertTrue((config.OUTPUT_DIR / "alerts.json").exists())
            
        except Exception as e:
            self.fail(f"Export failed: {e}")
        finally:
            agent.close()


def run_tests():
    """Run all tests and generate report"""
    print("="*70)
    print("🧪 Running Drone Security Agent Test Suite")
    print("="*70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTelemetrySimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoFrameSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameIndexer))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)