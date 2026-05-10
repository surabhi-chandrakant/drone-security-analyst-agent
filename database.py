"""
Database module for frame-by-frame indexing and querying
This implements the cross-domain requirement for video frame indexing
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import config


class FrameIndexer:
    """Handles frame-by-frame video indexing with advanced querying capabilities"""
    
    def __init__(self, db_path: Path = config.DATABASE_PATH):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Frames table - stores individual frame data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                frame_number INTEGER NOT NULL,
                telemetry_data TEXT NOT NULL,
                description TEXT NOT NULL,
                objects_detected TEXT,
                location TEXT,
                altitude REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Objects table - normalized object detection data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_id INTEGER NOT NULL,
                object_type TEXT NOT NULL,
                object_details TEXT,
                confidence REAL,
                location TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (frame_id) REFERENCES frames(id)
            )
        """)
        
        # Alerts table - security alerts generated
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (frame_id) REFERENCES frames(id)
            )
        """)
        
        # Events table - tracks recurring patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                first_occurrence TEXT NOT NULL,
                last_occurrence TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                related_objects TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for faster querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_frames_timestamp ON frames(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(object_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_objects_timestamp ON objects(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        self.conn.commit()
    
    def insert_frame(self, frame_data: Dict) -> int:
        """Insert a new frame into the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO frames (timestamp, frame_number, telemetry_data, description, 
                              objects_detected, location, altitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            frame_data['timestamp'],
            frame_data['frame_number'],
            json.dumps(frame_data['telemetry']),
            frame_data['description'],
            json.dumps(frame_data.get('objects', [])),
            frame_data['telemetry'].get('location', ''),
            frame_data['telemetry'].get('altitude', 0)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_object(self, frame_id: int, obj_data: Dict) -> int:
        """Insert detected object into database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO objects (frame_id, object_type, object_details, confidence, 
                               location, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            frame_id,
            obj_data['type'],
            json.dumps(obj_data.get('details', {})),
            obj_data.get('confidence', 0.0),
            obj_data.get('location', ''),
            obj_data['timestamp']
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_alert(self, alert_data: Dict) -> int:
        """Insert security alert into database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (frame_id, alert_type, severity, description, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            alert_data['frame_id'],
            alert_data['alert_type'],
            alert_data['severity'],
            alert_data['description'],
            alert_data['timestamp']
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def query_frames_by_time(self, start_time: str, end_time: str) -> List[Dict]:
        """Query frames within a time range"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM frames 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_time, end_time))
        return [dict(row) for row in cursor.fetchall()]
    
    def query_frames_by_object(self, object_type: str) -> List[Dict]:
        """Query all frames containing a specific object type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT f.* FROM frames f
            JOIN objects o ON f.id = o.frame_id
            WHERE o.object_type LIKE ?
            ORDER BY f.timestamp
        """, (f"%{object_type}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def query_objects_by_type(self, object_type: str) -> List[Dict]:
        """Get all detections of a specific object type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT o.*, f.timestamp as frame_timestamp, f.location as frame_location
            FROM objects o
            JOIN frames f ON o.frame_id = f.id
            WHERE o.object_type LIKE ?
            ORDER BY o.timestamp
        """, (f"%{object_type}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def query_alerts_by_type(self, alert_type: str) -> List[Dict]:
        """Get all alerts of a specific type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM alerts
            WHERE alert_type = ?
            ORDER BY timestamp DESC
        """, (alert_type,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_object_frequency(self, object_type: str) -> int:
        """Count occurrences of an object type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM objects
            WHERE object_type LIKE ?
        """, (f"%{object_type}%",))
        return cursor.fetchone()[0]
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get most recent alerts"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, f.description as frame_description
            FROM alerts a
            JOIN frames f ON a.frame_id = f.id
            ORDER BY a.timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_frames(self, query: str) -> List[Dict]:
        """Full-text search across frame descriptions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM frames
            WHERE description LIKE ?
            ORDER BY timestamp
        """, (f"%{query}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM frames")
        stats['total_frames'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM objects")
        stats['total_objects'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        stats['total_alerts'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT object_type, COUNT(*) as count
            FROM objects
            GROUP BY object_type
            ORDER BY count DESC
            LIMIT 5
        """)
        stats['top_objects'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()