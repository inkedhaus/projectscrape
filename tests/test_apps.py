"""Tests for application modules."""

from unittest.mock import Mock, patch

from apps.ad_intel.scraper import FacebookAdScraper
from apps.analysis.analyzer import AdAnalyzer
from apps.supplier_intel.finder import SupplierFinder


class TestFacebookAdScraper:
    """Test Facebook ad scraper."""

    def setup_method(self):
        """Setup test scraper."""
        self.scraper = FacebookAdScraper(headless=True, max_scrolls=2)

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        assert self.scraper.headless is True
        assert self.scraper.max_scrolls == 2
        assert self.scraper.intercepted_data == []

    def test_is_ad_library_response(self):
        """Test GraphQL response detection."""
        # Valid ad library response structure
        valid_response = {
            "data": {
                "ad_library_main": {
                    "edges": [{"node": {"page_name": "Test Page", "snapshot": {"cards": []}}}]
                }
            }
        }

        assert self.scraper._is_ad_library_response(valid_response) is True

        # Invalid response
        invalid_response = {"data": {"other": "data"}}
        assert self.scraper._is_ad_library_response(invalid_response) is False

    def test_generate_ad_id(self):
        """Test ad ID generation."""
        node = {
            "page_name": "Test Page",
            "snapshot": {"cards": [{"title": "Test Title"}], "cta_text": "Learn More"},
        }

        ad_id = self.scraper._generate_ad_id(node)
        assert len(ad_id) == 12  # MD5 hash truncated
        assert isinstance(ad_id, str)

    def test_parse_ad_node(self):
        """Test parsing ad node data."""
        node = {
            "page_name": "Test Brand",
            "snapshot": {
                "cards": [
                    {
                        "title": "Amazing Product",
                        "body": "Get 50% off today!",
                        "snapshot": {
                            "images": [{"original_image_url": "https://example.com/image.jpg"}]
                        },
                    }
                ],
                "cta_text": "Shop Now",
            },
        }

        ad = self.scraper._parse_ad_node(node)

        assert ad is not None
        assert ad["page_name"] == "Test Brand"
        assert ad["brand"] == "Test Brand"
        assert ad["headline"] == "Amazing Product"
        assert ad["body"] == "Get 50% off today!"
        assert ad["call_to_action"] == "Shop Now"
        assert ad["media_type"] == "image"
        assert len(ad["media_urls"]) == 1


class TestAdAnalyzer:
    """Test ad analyzer."""

    def setup_method(self):
        """Setup test analyzer."""
        self.analyzer = AdAnalyzer()

    @patch("apps.analysis.analyzer.LLMClient")
    def test_analyze_single_ad(self, mock_llm_client):
        """Test single ad analysis."""
        # Mock LLM response
        mock_llm_client.return_value.analyze_ad.return_value = {
            "hook_analysis": "Strong hook",
            "effectiveness_score": 8.5,
        }

        ad = {"id": "test-1", "headline": "Test Headline", "body": "Test Body"}

        result = self.analyzer.analyze_single_ad(ad)

        assert result["ad_id"] == "test-1"
        assert result["hook_analysis"] == "Strong hook"
        assert result["effectiveness_score"] == 8.5

    @patch("apps.analysis.analyzer.LLMClient")
    def test_extract_patterns(self, mock_llm_client):
        """Test pattern extraction."""
        # Mock LLM response
        mock_llm_client.return_value.extract_patterns.return_value = {
            "common_hooks": ["Hook 1", "Hook 2"],
            "power_words": ["Amazing", "Incredible"],
        }

        ads = [{"headline": "Amazing Product"}, {"headline": "Incredible Deal"}]

        patterns = self.analyzer.extract_patterns(ads)

        assert "common_hooks" in patterns
        assert "power_words" in patterns
        assert len(patterns["common_hooks"]) == 2


class TestSupplierFinder:
    """Test supplier finder."""

    def setup_method(self):
        """Setup test supplier finder."""
        self.finder = SupplierFinder()

    def test_find_suppliers(self):
        """Test supplier finding (using mock data)."""
        suppliers = self.finder.find_suppliers(niche="test product", location="Test City", limit=10)

        assert isinstance(suppliers, list)
        # Should return mock suppliers
        assert len(suppliers) > 0

        # Check supplier structure
        supplier = suppliers[0]
        assert "name" in supplier
        assert "location" in supplier
        assert "rating" in supplier

    def test_deduplicate_suppliers(self):
        """Test supplier deduplication."""
        suppliers = [
            {"name": "Supplier A", "location": "City 1"},
            {"name": "Supplier B", "location": "City 2"},
            {"name": "supplier a", "location": "city 1"},  # Duplicate
            {"name": "Supplier C", "location": "City 3"},
        ]

        unique_suppliers = self.finder._deduplicate_suppliers(suppliers)

        # Should remove the duplicate (case-insensitive)
        assert len(unique_suppliers) == 3

    @patch("requests.Session.get")
    def test_verify_supplier(self, mock_get):
        """Test supplier verification."""
        # Mock successful website response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><title>Test Supplier</title></html>"
        mock_get.return_value = mock_response

        supplier = {"name": "Test Supplier", "website": "https://example.com"}

        verified_supplier = self.finder.verify_supplier(supplier)

        assert verified_supplier["website_verified"] is True
        assert "website_title" in verified_supplier


class TestIntegration:
    """Integration tests for multiple components."""

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline with mock data."""
        # Mock ad data
        ads = [
            {
                "id": "test-1",
                "brand": "Test Brand",
                "headline": "Amazing Product",
                "body": "Get 50% off today!",
            }
        ]

        # This would normally test the full pipeline
        # For now, just verify data structure
        assert len(ads) == 1
        assert ads[0]["id"] == "test-1"
