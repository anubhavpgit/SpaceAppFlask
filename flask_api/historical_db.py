"""
Simple historical data storage using SQLite
Stores daily AQI measurements for trend analysis
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class HistoricalDataStore:
    """Store and retrieve historical AQI measurements"""

    def __init__(self, db_path='data/historical.db'):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                aqi INTEGER NOT NULL,
                category TEXT NOT NULL,
                pollutants TEXT,
                source TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(date, latitude, longitude)
            )
        ''')

        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_location_date
            ON daily_measurements(latitude, longitude, date DESC)
        ''')

        conn.commit()
        conn.close()

    def store_measurement(self, lat: float, lon: float, aqi: int, category: str,
                         pollutants: Dict[str, float], source: str = 'api'):
        """Store a daily measurement (one per day per location)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Use today's date as the key
        today = datetime.utcnow().strftime('%Y-%m-%d')

        # Round coordinates to 2 decimals to group nearby locations
        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_measurements
                (date, latitude, longitude, aqi, category, pollutants, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today,
                lat_rounded,
                lon_rounded,
                aqi,
                category,
                json.dumps(pollutants),
                source,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error storing measurement: {e}")
        finally:
            conn.close()

    def get_historical_data(self, lat: float, lon: float, days: int = 7) -> List[Dict[str, Any]]:
        """Get historical data for a location"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Round coordinates to match storage
        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        cursor.execute('''
            SELECT date, aqi, category, pollutants, created_at
            FROM daily_measurements
            WHERE latitude = ? AND longitude = ?
            AND date >= ? AND date <= ?
            ORDER BY date ASC
        ''', (
            lat_rounded,
            lon_rounded,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))

        rows = cursor.fetchall()
        conn.close()

        measurements = []
        for row in rows:
            date_str, aqi, category, pollutants_json, created_at = row
            measurements.append({
                'timestamp': f"{date_str}T12:00:00Z",  # Noon of each day
                'aqi': aqi,
                'category': category,
                'pollutants': json.loads(pollutants_json) if pollutants_json else {},
                'dayLabel': datetime.fromisoformat(date_str).strftime('%b %d')
            })

        return measurements

    def get_data_count(self, lat: float, lon: float) -> int:
        """Get number of days of data available"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)

        cursor.execute('''
            SELECT COUNT(*) FROM daily_measurements
            WHERE latitude = ? AND longitude = ?
        ''', (lat_rounded, lon_rounded))

        count = cursor.fetchone()[0]
        conn.close()
        return count


# Global instance
historical_store = HistoricalDataStore()
