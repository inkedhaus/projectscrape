"""Database operations for AdSpy Marketing Suite."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import load_config


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str | None = None):
        self.config = load_config()
        self.db_path = db_path or self.config.db_path
        self._ensure_db_dir()
        self._init_tables()

    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_tables(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ads (
                    id TEXT PRIMARY KEY,
                    brand TEXT,
                    page_name TEXT,
                    headline TEXT,
                    body TEXT,
                    call_to_action TEXT,
                    media_type TEXT,
                    media_urls TEXT,
                    target_audience TEXT,
                    created_date TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_id TEXT,
                    analysis_type TEXT,
                    insights TEXT,
                    score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ad_id) REFERENCES ads (id)
                )
            """
            )

    def save_ads(self, ads: list[dict[str, Any]]) -> int:
        """Save scraped ads to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            saved_count = 0

            for ad in ads:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ads
                        (id, brand, page_name, headline, body, call_to_action,
                         media_type, media_urls, target_audience, created_date, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            ad.get("id", ""),
                            ad.get("brand", ""),
                            ad.get("page_name", ""),
                            ad.get("headline", ""),
                            ad.get("body", ""),
                            ad.get("call_to_action", ""),
                            ad.get("media_type", ""),
                            json.dumps(ad.get("media_urls", [])),
                            json.dumps(ad.get("target_audience", {})),
                            ad.get("created_date", ""),
                            json.dumps(ad),
                        ),
                    )
                    saved_count += 1
                except sqlite3.Error as e:
                    print(f"Error saving ad {ad.get('id', 'unknown')}: {e}")

            conn.commit()
            return saved_count

    def get_ads(self, limit: int | None = None, brand: str | None = None) -> list[dict[str, Any]]:
        """Retrieve ads from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM ads"
            params = []

            if brand:
                query += " WHERE brand LIKE ?"
                params.append(f"%{brand}%")

            query += " ORDER BY scraped_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def save_analysis(
        self, ad_id: str, analysis_type: str, insights: dict[str, Any], score: float = 0.0
    ):
        """Save analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO analysis (ad_id, analysis_type, insights, score)
                VALUES (?, ?, ?, ?)
            """,
                (ad_id, analysis_type, json.dumps(insights), score),
            )
            conn.commit()

    def get_analysis(self, ad_id: str | None = None) -> list[dict[str, Any]]:
        """Retrieve analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if ad_id:
                cursor.execute("SELECT * FROM analysis WHERE ad_id = ?", (ad_id,))
            else:
                cursor.execute("SELECT * FROM analysis ORDER BY created_at DESC")

            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM ads")
            total_ads = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT brand) FROM ads")
            unique_brands = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM analysis")
            total_analysis = cursor.fetchone()[0]

            return {
                "total_ads": total_ads,
                "unique_brands": unique_brands,
                "total_analysis": total_analysis,
            }
