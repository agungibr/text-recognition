"""
Database Service Module
Handles SQLite database operations for storing examination results.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional


class DatabaseService:
    """SQLite database service for radiology reader application."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = "radiology_reader.db"
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _init_database(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS examinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                image_name TEXT,
                processed_at TEXT NOT NULL,
                detection_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                examination_id INTEGER NOT NULL,
                x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER,
                confidence REAL,
                text_content TEXT,
                FOREIGN KEY (examination_id) REFERENCES examinations(id)
            )
        """)

        conn.commit()

    def save_examination(self, image_path: str, image_name: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO examinations (image_path, image_name, processed_at) VALUES (?, ?, ?)",
            (image_path, image_name, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid

    def save_detection(self, examination_id: int, x1: int, y1: int, x2: int, y2: int,
                      confidence: float, text_content: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO detections (examination_id, x1, y1, x2, y2, confidence, text_content) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (examination_id, x1, y1, x2, y2, confidence, text_content)
        )
        conn.commit()
        return cursor.lastrowid

    def get_examination(self, examination_id: int) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM examinations WHERE id = ?", (examination_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_examination_detections(self, examination_id: int) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detections WHERE examination_id = ?", (examination_id,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
