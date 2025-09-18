import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.models import CompetitorAd
from ..services.scraper import CompetitorAdsScraper

router = APIRouter()
logger = logging.getLogger(__name__)

# Background task storage
task_storage = {}


async def run_ad_scraping(task_id: str, brands: list[str], platforms: list[str], analyze: bool):
    """Background task for ad scraping"""
    try:
        task_storage[task_id] = {
            "status": "running",
            "progress": 0,
            "message": "Starting ad scraping...",
        }

        # Use Firecrawl-powered scraper
        scraper = CompetitorAdsScraper(
            firecrawl_api_key=settings.firecrawl_api_key, openai_api_key=settings.openai_api_key
        )
        all_ads = []

        total_brands = len(brands)
        for i, brand in enumerate(brands):

            task_storage[task_id]["message"] = f"Scraping ads for {brand}..."
            task_storage[task_id]["progress"] = (i / total_brands) * 70

            # Scrape Facebook ads with Firecrawl
            if "facebook" in platforms:
                logger.info(f"Scraping Facebook ads for {brand}")
                fb_ads = await scraper.scrape_facebook_ads(brand)
                all_ads.extend(fb_ads)
                logger.info(f"Found {len(fb_ads)} Facebook ads for {brand}")

            # TikTok scraping still uses mock data for now
            if "tiktok" in platforms:
                tiktok_ads = [
                    {
                        "platform": "tiktok",
                        "brand": brand,
                        "ad_id": f"{brand}_tiktok_{i}",
                        "copy": f"Sample TikTok ad copy for {brand}",
                        "cta": "Learn More",
                        "status": "active",
                        "likes": 200 + i * 15,
                        "shares": 30 + i * 3,
                        "comments": 25 + i,
                    }
                ]
                all_ads.extend(tiktok_ads)

        task_storage[task_id]["progress"] = 60
        task_storage[task_id]["message"] = "Saving ads to database..."

        # Save to database
        db = next(get_db())
        try:
            saved_ads = []
            for ad_data in all_ads:
                # Check if ad already exists
                existing = (
                    db.query(CompetitorAd)
                    .filter(CompetitorAd.ad_id == ad_data.get("ad_id"))
                    .first()
                )

                if not existing:
                    ad = CompetitorAd(
                        platform=ad_data.get("platform"),
                        brand=ad_data.get("brand"),
                        ad_id=ad_data.get("ad_id"),
                        copy=ad_data.get("copy"),
                        cta=ad_data.get("cta"),
                        status=ad_data.get("status", "active"),
                        media_urls=ad_data.get("media_urls", []),
                        likes=ad_data.get("likes", 0),
                        shares=ad_data.get("shares", 0),
                        comments=ad_data.get("comments", 0),
                    )
                    db.add(ad)
                    saved_ads.append(ad_data)

            db.commit()

            task_storage[task_id] = {
                "status": "completed",
                "progress": 100,
                "message": f"Successfully scraped {len(saved_ads)} new ads",
                "result": {
                    "total_scraped": len(all_ads),
                    "new_ads": len(saved_ads),
                    "analyzed": analyze,
                },
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in ad scraping task {task_id}: {e}")
        task_storage[task_id] = {
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}",
            "error": str(e),
        }


@router.post("/scrape")
async def scrape_competitor_ads(
    brands: list[str],
    platforms: list[str] = Query(default=["facebook", "tiktok"]),
    analyze: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Scrape competitor ads from multiple platforms"""

    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_ad_scraping, task_id, brands, platforms, analyze)

    return {
        "task_id": task_id,
        "brands": brands,
        "platforms": platforms,
        "check_status_at": f"/api/ads/tasks/{task_id}/status",
    }


@router.get("/tasks/{task_id}/status")
async def get_scraping_task_status(task_id: str):
    """Get status of ad scraping task"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_storage[task_id]


@router.get("/")
async def list_ads(
    skip: int = 0,
    limit: int = 100,
    platform: str | None = None,
    brand: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List competitor ads with filtering"""

    query = db.query(CompetitorAd)

    if platform:
        query = query.filter(CompetitorAd.platform == platform)

    if brand:
        query = query.filter(CompetitorAd.brand.ilike(f"%{brand}%"))

    if status:
        query = query.filter(CompetitorAd.status == status)

    ads = query.offset(skip).limit(limit).all()

    return {"ads": ads, "count": len(ads), "skip": skip, "limit": limit}


@router.post("/{ad_id}/analyze")
async def analyze_ad(
    ad_id: int,
    generate_variations: bool = False,
    num_variations: int = 5,
    db: Session = Depends(get_db),
):
    """Deep AI analysis of a competitor ad"""

    ad = db.query(CompetitorAd).filter(CompetitorAd.id == ad_id).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # TODO: Integrate with existing AI analyzer
    analysis = {
        "psychological_triggers": ["urgency", "social_proof"],
        "hooks_identified": ["question_hook", "benefit_hook"],
        "risk_level": "low",
        "effectiveness_score": 8.5,
    }

    # Save analysis
    ad.ai_analysis = analysis
    db.commit()

    result = {"ad_id": ad_id, "analysis": analysis}

    # TODO: Generate variations if requested
    if generate_variations:
        variations = [
            {"copy": f"Variation {i} of {ad.copy}", "cta": ad.cta} for i in range(num_variations)
        ]
        result["variations"] = variations

    return result


@router.get("/{ad_id}")
async def get_ad(ad_id: int, db: Session = Depends(get_db)):
    """Get a single ad by ID"""

    ad = db.query(CompetitorAd).filter(CompetitorAd.id == ad_id).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    return ad


@router.delete("/{ad_id}")
async def delete_ad(ad_id: int, db: Session = Depends(get_db)):
    """Delete an ad"""

    ad = db.query(CompetitorAd).filter(CompetitorAd.id == ad_id).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    db.delete(ad)
    db.commit()

    return {"message": "Ad deleted successfully"}


@router.get("/brands/top")
async def get_top_brands(limit: int = 10, db: Session = Depends(get_db)):
    """Get top brands by ad count"""

    from sqlalchemy import func

    results = (
        db.query(CompetitorAd.brand, func.count(CompetitorAd.id).label("ad_count"))
        .group_by(CompetitorAd.brand)
        .order_by(func.count(CompetitorAd.id).desc())
        .limit(limit)
        .all()
    )

    return {
        "top_brands": [{"brand": result.brand, "ad_count": result.ad_count} for result in results]
    }
