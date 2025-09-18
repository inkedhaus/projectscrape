"""Test configuration and fixtures."""

import os
import tempfile
from pathlib import Path

import pytest

from core.db import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    db = Database(temp_file.name)
    yield db
    os.unlink(temp_file.name)


@pytest.fixture
def sample_ads():
    """Sample ad data for testing."""
    return [
        {
            "id": "ad-001",
            "brand": "TechCorp",
            "page_name": "TechCorp Official",
            "headline": "Revolutionary Tech Product",
            "body": "Transform your workflow with our cutting-edge solution. Save 40% today!",
            "call_to_action": "Learn More",
            "media_type": "image",
            "media_urls": ["https://example.com/image1.jpg"],
            "created_date": "2024-01-15",
        },
        {
            "id": "ad-002",
            "brand": "FashionCo",
            "page_name": "FashionCo Store",
            "headline": "Summer Collection 2024",
            "body": "Discover the hottest trends this season. Free shipping on orders over $100.",
            "call_to_action": "Shop Now",
            "media_type": "video",
            "media_urls": ["https://example.com/video1.mp4"],
            "created_date": "2024-01-10",
        },
        {
            "id": "ad-003",
            "brand": "HealthPlus",
            "page_name": "HealthPlus Wellness",
            "headline": "Natural Health Solutions",
            "body": "Boost your energy naturally with our premium supplements. Trusted by thousands.",
            "call_to_action": "Try Now",
            "media_type": "image",
            "media_urls": ["https://example.com/image2.jpg", "https://example.com/image3.jpg"],
            "created_date": "2024-01-12",
        },
    ]


@pytest.fixture
def sample_analysis():
    """Sample analysis data for testing."""
    return [
        {
            "ad_id": "ad-001",
            "hook_analysis": 'Strong opening with "Revolutionary" creates curiosity',
            "angle": "Innovation and efficiency",
            "pain_points": ["Inefficient workflow", "Outdated tools"],
            "benefits": ["Improved productivity", "Cost savings"],
            "emotion": "excitement",
            "target_audience": "Business professionals",
            "effectiveness_score": 8.5,
            "improvements": ["Add social proof", "Include specific metrics"],
        },
        {
            "ad_id": "ad-002",
            "hook_analysis": 'Seasonal relevance with "Summer Collection" is timely',
            "angle": "Fashion trends and convenience",
            "pain_points": ["Outdated wardrobe", "High shipping costs"],
            "benefits": ["Trendy appearance", "Free shipping"],
            "emotion": "desire",
            "target_audience": "Fashion-conscious consumers",
            "effectiveness_score": 7.2,
            "improvements": ["Highlight unique styles", "Show before/after"],
        },
    ]


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup handled by tempfile


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "hook_analysis": "Compelling hook that captures attention",
        "angle": "Problem-solution focused",
        "pain_points": ["Time constraints", "Budget concerns"],
        "benefits": ["Time savings", "Cost efficiency"],
        "emotion": "relief",
        "target_audience": "Small business owners",
        "effectiveness_score": 7.8,
        "improvements": ["Add urgency", "Include testimonials"],
    }
