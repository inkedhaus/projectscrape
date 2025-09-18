"""Tests for core modules."""

import os
import tempfile
from unittest.mock import patch

from core.config import Config, load_config
from core.db import Database
from core.schemas import Ad, AdAnalysis


class TestConfig:
    """Test configuration management."""

    def test_config_creation(self):
        """Test Config dataclass creation."""
        config = Config(openai_api_key="test-key")
        assert config.openai_api_key == "test-key"
        assert config.openai_model == "gpt-4o-mini"
        assert config.max_scrolls == 10

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-key", "MAX_SCROLLS": "20", "HEADLESS": "false"})
    def test_load_config(self):
        """Test loading config from environment."""
        config = load_config()
        assert config.openai_api_key == "env-key"
        assert config.max_scrolls == 20
        assert config.headless is False


class TestDatabase:
    """Test database operations."""

    def setup_method(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database."""
        os.unlink(self.temp_db.name)

    def test_save_and_get_ads(self):
        """Test saving and retrieving ads."""
        test_ads = [
            {
                "id": "test-1",
                "brand": "Test Brand",
                "headline": "Test Headline",
                "body": "Test body content",
            }
        ]

        saved_count = self.db.save_ads(test_ads)
        assert saved_count == 1

        retrieved_ads = self.db.get_ads()
        assert len(retrieved_ads) == 1
        assert retrieved_ads[0]["brand"] == "Test Brand"

    def test_save_analysis(self):
        """Test saving analysis results."""
        self.db.save_analysis(
            ad_id="test-1", analysis_type="ai_analysis", insights={"score": 8.5}, score=8.5
        )

        analysis = self.db.get_analysis(ad_id="test-1")
        assert len(analysis) == 1
        assert analysis[0]["score"] == 8.5

    def test_get_stats(self):
        """Test database statistics."""
        # Add test data
        test_ads = [
            {"id": "test-1", "brand": "Brand A"},
            {"id": "test-2", "brand": "Brand B"},
            {"id": "test-3", "brand": "Brand A"},
        ]
        self.db.save_ads(test_ads)

        stats = self.db.get_stats()
        assert stats["total_ads"] == 3
        assert stats["unique_brands"] == 2


class TestSchemas:
    """Test data schemas."""

    def test_ad_schema(self):
        """Test Ad dataclass."""
        ad = Ad(
            id="test-1",
            brand="Test Brand",
            page_name="Test Page",
            headline="Test Headline",
            body="Test Body",
            call_to_action="Learn More",
            media_type="image",
        )

        assert ad.id == "test-1"
        assert ad.brand == "Test Brand"
        assert ad.media_urls == []  # default empty list

    def test_ad_analysis_schema(self):
        """Test AdAnalysis dataclass."""
        analysis = AdAnalysis(
            ad_id="test-1",
            hook_analysis="Strong opening hook",
            angle="Pain point focus",
            pain_points=["Problem 1", "Problem 2"],
            benefits=["Benefit 1", "Benefit 2"],
            emotion="urgency",
            target_audience="Young professionals",
            effectiveness_score=8.5,
            improvements=["Improvement 1"],
        )

        assert analysis.ad_id == "test-1"
        assert analysis.effectiveness_score == 8.5
        assert len(analysis.pain_points) == 2
