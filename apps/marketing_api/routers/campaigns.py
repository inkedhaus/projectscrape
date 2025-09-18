import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Campaign, CompetitorAd, Supplier

router = APIRouter()
logger = logging.getLogger(__name__)


class CampaignCreate(BaseModel):
    name: str
    platform: str
    angle: str
    target_audience: dict
    budget_daily: float
    budget_total: float | None = None
    supplier_id: int | None = None
    source_ad_id: int | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    budget_daily: float | None = None
    budget_total: float | None = None


@router.post("/")
async def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new marketing campaign"""

    # Validate supplier exists if provided
    if campaign.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == campaign.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")

    # Validate source ad exists if provided
    if campaign.source_ad_id:
        source_ad = db.query(CompetitorAd).filter(CompetitorAd.id == campaign.source_ad_id).first()
        if not source_ad:
            raise HTTPException(status_code=404, detail="Source ad not found")

    db_campaign = Campaign(
        name=campaign.name,
        platform=campaign.platform,
        status="draft",
        angle=campaign.angle,
        target_audience=campaign.target_audience,
        budget_daily=campaign.budget_daily,
        budget_total=campaign.budget_total,
        supplier_id=campaign.supplier_id,
        source_ad_id=campaign.source_ad_id,
    )

    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)

    return db_campaign


@router.get("/")
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    platform: str | None = None,
    db: Session = Depends(get_db),
):
    """List campaigns with filtering"""

    query = db.query(Campaign)

    if status:
        query = query.filter(Campaign.status == status)

    if platform:
        query = query.filter(Campaign.platform == platform)

    campaigns = query.offset(skip).limit(limit).all()

    return {"campaigns": campaigns, "count": len(campaigns), "skip": skip, "limit": limit}


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a single campaign by ID"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: int, campaign_update: CampaignUpdate, db: Session = Depends(get_db)
):
    """Update a campaign"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = campaign_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)

    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Delete a campaign"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()

    return {"message": "Campaign deleted successfully"}


@router.post("/{campaign_id}/launch")
async def launch_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Launch a campaign (change status to active)"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != "draft":
        raise HTTPException(status_code=400, detail="Campaign must be in draft status to launch")

    campaign.status = "testing"
    db.commit()

    return {"message": "Campaign launched successfully", "campaign": campaign}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Pause a campaign"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == "ended":
        raise HTTPException(status_code=400, detail="Cannot pause ended campaign")

    campaign.status = "paused"
    db.commit()

    return {"message": "Campaign paused successfully", "campaign": campaign}


@router.get("/{campaign_id}/performance")
async def get_campaign_performance(campaign_id: int, db: Session = Depends(get_db)):
    """Get campaign performance metrics"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Calculate performance metrics
    ctr = (campaign.clicks / campaign.impressions * 100) if campaign.impressions > 0 else 0
    cvr = (campaign.conversions / campaign.clicks * 100) if campaign.clicks > 0 else 0
    cpc = (campaign.spend / campaign.clicks) if campaign.clicks > 0 else 0
    cpa = (campaign.spend / campaign.conversions) if campaign.conversions > 0 else 0
    roas = (campaign.revenue / campaign.spend) if campaign.spend > 0 else 0

    return {
        "campaign_id": campaign_id,
        "metrics": {
            "spend": campaign.spend,
            "impressions": campaign.impressions,
            "clicks": campaign.clicks,
            "conversions": campaign.conversions,
            "revenue": campaign.revenue,
            "ctr": round(ctr, 2),
            "cvr": round(cvr, 2),
            "cpc": round(cpc, 2),
            "cpa": round(cpa, 2),
            "roas": round(roas, 2),
        },
    }
