import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.models import Campaign

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_performance_dashboard(
    days: int = Query(default=30, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """Get overall performance dashboard metrics"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Campaign metrics
    campaigns_query = db.query(Campaign).filter(Campaign.created_at >= start_date)

    total_campaigns = campaigns_query.count()
    active_campaigns = campaigns_query.filter(Campaign.status == "testing").count()
    paused_campaigns = campaigns_query.filter(Campaign.status == "paused").count()

    # Performance aggregates
    performance_data = (
        db.query(
            func.sum(Campaign.spend).label("total_spend"),
            func.sum(Campaign.impressions).label("total_impressions"),
            func.sum(Campaign.clicks).label("total_clicks"),
            func.sum(Campaign.conversions).label("total_conversions"),
            func.sum(Campaign.revenue).label("total_revenue"),
        )
        .filter(Campaign.created_at >= start_date)
        .first()
    )

    total_spend = performance_data.total_spend or 0
    total_impressions = performance_data.total_impressions or 0
    total_clicks = performance_data.total_clicks or 0
    total_conversions = performance_data.total_conversions or 0
    total_revenue = performance_data.total_revenue or 0

    # Calculate overall metrics
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    overall_cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    overall_cpc = total_spend / total_clicks if total_clicks > 0 else 0
    overall_cpa = total_spend / total_conversions if total_conversions > 0 else 0
    overall_roas = total_revenue / total_spend if total_spend > 0 else 0

    # Top performing campaigns
    top_campaigns = (
        db.query(Campaign)
        .filter(and_(Campaign.created_at >= start_date, Campaign.roas.isnot(None)))
        .order_by(Campaign.roas.desc())
        .limit(5)
        .all()
    )

    return {
        "period": f"{days} days",
        "campaign_summary": {
            "total": total_campaigns,
            "active": active_campaigns,
            "paused": paused_campaigns,
        },
        "overall_metrics": {
            "spend": round(total_spend, 2),
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "revenue": round(total_revenue, 2),
            "ctr": round(overall_ctr, 2),
            "cvr": round(overall_cvr, 2),
            "cpc": round(overall_cpc, 2),
            "cpa": round(overall_cpa, 2),
            "roas": round(overall_roas, 2),
        },
        "top_campaigns": [
            {
                "id": campaign.id,
                "name": campaign.name,
                "roas": campaign.roas,
                "spend": campaign.spend,
                "revenue": campaign.revenue,
            }
            for campaign in top_campaigns
        ],
    }


@router.get("/campaigns/{campaign_id}/history")
async def get_campaign_performance_history(
    campaign_id: int,
    days: int = Query(default=30, description="Number of days of history"),
    db: Session = Depends(get_db),
):
    """Get historical performance data for a campaign"""

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # For now, return mock historical data
    # TODO: Implement actual historical tracking
    history = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        history.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "spend": campaign.spend / days if campaign.spend else 0,
                "clicks": campaign.clicks // days if campaign.clicks else 0,
                "conversions": campaign.conversions // days if campaign.conversions else 0,
                "revenue": campaign.revenue / days if campaign.revenue else 0,
            }
        )

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "history": list(reversed(history)),
    }


@router.get("/alerts")
async def get_performance_alerts(db: Session = Depends(get_db)):
    """Get performance alerts based on thresholds"""

    alerts = []

    # Check campaigns with high CPA
    high_cpa_campaigns = (
        db.query(Campaign)
        .filter(
            and_(
                Campaign.status.in_(["testing", "scaling"]),
                Campaign.cpa > settings.default_cpa_threshold,
            )
        )
        .all()
    )

    for campaign in high_cpa_campaigns:
        alerts.append(
            {
                "type": "high_cpa",
                "severity": "warning",
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "message": f"CPA of ${campaign.cpa:.2f} exceeds threshold of ${settings.default_cpa_threshold}",
                "current_value": campaign.cpa,
                "threshold": settings.default_cpa_threshold,
            }
        )

    # Check campaigns with low ROAS
    low_roas_campaigns = (
        db.query(Campaign)
        .filter(
            and_(
                Campaign.status.in_(["testing", "scaling"]),
                Campaign.roas < settings.default_roas_threshold,
                Campaign.roas.isnot(None),
            )
        )
        .all()
    )

    for campaign in low_roas_campaigns:
        alerts.append(
            {
                "type": "low_roas",
                "severity": "critical",
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "message": f"ROAS of {campaign.roas:.2f} is below threshold of {settings.default_roas_threshold}",
                "current_value": campaign.roas,
                "threshold": settings.default_roas_threshold,
            }
        )

    return {"alerts": alerts, "count": len(alerts)}


@router.get("/compare")
async def compare_campaigns(
    campaign_ids: list[int] = Query(..., description="List of campaign IDs to compare"),
    db: Session = Depends(get_db),
):
    """Compare performance metrics across multiple campaigns"""

    campaigns = db.query(Campaign).filter(Campaign.id.in_(campaign_ids)).all()

    if len(campaigns) != len(campaign_ids):
        found_ids = [c.id for c in campaigns]
        missing_ids = [cid for cid in campaign_ids if cid not in found_ids]
        raise HTTPException(status_code=404, detail=f"Campaigns not found: {missing_ids}")

    comparison_data = []
    for campaign in campaigns:
        ctr = (campaign.clicks / campaign.impressions * 100) if campaign.impressions > 0 else 0
        cvr = (campaign.conversions / campaign.clicks * 100) if campaign.clicks > 0 else 0
        cpc = (campaign.spend / campaign.clicks) if campaign.clicks > 0 else 0
        cpa = (campaign.spend / campaign.conversions) if campaign.conversions > 0 else 0
        roas = (campaign.revenue / campaign.spend) if campaign.spend > 0 else 0

        comparison_data.append(
            {
                "campaign_id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "platform": campaign.platform,
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
        )

    return {"comparison": comparison_data, "campaign_count": len(campaigns)}


@router.get("/trends")
async def get_performance_trends(
    metric: str = Query(default="roas", description="Metric to analyze trends for"),
    days: int = Query(default=30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """Get performance trends for a specific metric"""

    valid_metrics = ["roas", "cpa", "ctr", "cvr", "spend"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400, detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
        )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    campaigns = db.query(Campaign).filter(Campaign.created_at >= start_date).all()

    # For now, return mock trend data
    # TODO: Implement actual trend analysis with time series data
    trend_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)

        # Calculate daily aggregate for the metric
        daily_value = 0
        if metric == "roas":
            daily_value = sum(c.roas or 0 for c in campaigns) / len(campaigns) if campaigns else 0
        elif metric == "cpa":
            daily_value = sum(c.cpa or 0 for c in campaigns) / len(campaigns) if campaigns else 0
        elif metric == "spend":
            daily_value = sum(c.spend or 0 for c in campaigns) if campaigns else 0

        trend_data.append({"date": date.strftime("%Y-%m-%d"), "value": round(daily_value, 2)})

    return {"metric": metric, "period": f"{days} days", "trend_data": trend_data}
