from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    website = Column(String, index=True)
    domain = Column(String, index=True)  # Normalized domain for dedup
    category = Column(String, index=True)

    # Quality metrics
    rating = Column(Float)
    reviews_count = Column(Integer)
    quality_score = Column(Float)  # 0-100
    has_ssl = Column(Boolean, default=False)
    has_contact = Column(Boolean, default=False)
    has_pricing = Column(Boolean, default=False)

    # Business details
    moq = Column(String)
    price_min = Column(Float)
    price_max = Column(Float)
    lead_time = Column(String)

    # Contact info
    emails = Column(JSON)  # List of emails
    phones = Column(JSON)  # List of phones
    contact_form_url = Column(String)

    # Location
    street = Column(String)
    city = Column(String, index=True)
    state = Column(String, index=True)
    country = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)

    # Meta
    sources = Column(JSON)
    scraped_at = Column(DateTime, server_default=func.now())
    last_verified = Column(DateTime)
    notes = Column(Text)

    # Relationships
    campaigns = relationship("Campaign", back_populates="supplier")


class CompetitorAd(Base):
    __tablename__ = "competitor_ads"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)  # facebook, tiktok, google
    brand = Column(String, index=True)
    ad_id = Column(String, unique=True, index=True)

    # Ad content
    headline = Column(String)
    copy = Column(Text)
    cta = Column(String)
    display_url = Column(String)
    landing_url = Column(String)

    # Media
    media_type = Column(String)  # image, video, carousel
    media_urls = Column(JSON)
    thumbnail_url = Column(String)
    video_transcript = Column(Text)

    # Performance metrics
    likes = Column(Integer)
    shares = Column(Integer)
    comments = Column(Integer)
    views = Column(Integer)
    ctr = Column(Float)

    # Status
    status = Column(String)  # active, paused, ended
    started_date = Column(DateTime)
    ended_date = Column(DateTime)
    last_seen = Column(DateTime)

    # Analysis
    ai_analysis = Column(JSON)  # Stored AI analysis
    hooks_identified = Column(JSON)
    psychological_triggers = Column(JSON)
    risk_flags = Column(JSON)

    # Meta
    scraped_at = Column(DateTime, server_default=func.now())
    analyzed_at = Column(DateTime)

    # Relationships
    campaigns = relationship("Campaign", back_populates="source_ad")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    platform = Column(String)
    status = Column(String)  # draft, testing, scaling, paused, ended

    # Strategy
    angle = Column(String)
    target_audience = Column(JSON)
    budget_daily = Column(Float)
    budget_total = Column(Float)

    # Performance
    spend = Column(Float, default=0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0)

    # Calculated metrics
    ctr = Column(Float)
    cvr = Column(Float)
    cpc = Column(Float)
    cpa = Column(Float)
    roas = Column(Float)

    # Relationships
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier = relationship("Supplier", back_populates="campaigns")

    source_ad_id = Column(Integer, ForeignKey("competitor_ads.id"))
    source_ad = relationship("CompetitorAd", back_populates="campaigns")

    # Meta
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    launched_at = Column(DateTime)
    ended_at = Column(DateTime)


class AdCreative(Base):
    __tablename__ = "ad_creatives"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    name = Column(String)
    type = Column(String)  # image, video, carousel, collection

    # Content
    headline = Column(String)
    body = Column(Text)
    cta = Column(String)

    # Media
    media_urls = Column(JSON)

    # Performance
    status = Column(String)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)

    # Testing
    is_control = Column(Boolean, default=False)
    test_group = Column(String)

    created_at = Column(DateTime, server_default=func.now())


class Task(Base):
    """Background task tracking"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)  # UUID
    name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    result = Column(JSON)
    error = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
