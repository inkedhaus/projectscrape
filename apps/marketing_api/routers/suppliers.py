import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Supplier

router = APIRouter()
logger = logging.getLogger(__name__)

# Background task storage (in production, use Redis/Celery)
task_storage = {}


async def run_deep_scrape(
    task_id: str, keyword: str, limit: int, enrich_contacts: bool, quality_threshold: int
):
    """Background task for deep supplier scraping"""
    try:
        # Update task status
        task_storage[task_id] = {
            "status": "running",
            "progress": 0,
            "message": "Starting supplier scrape...",
        }

        # Placeholder for actual scraper integration
        # TODO: Integrate with existing supplier_intel app

        task_storage[task_id]["progress"] = 25
        task_storage[task_id]["message"] = "Searching suppliers..."

        # Mock supplier data for now
        suppliers = [
            {
                "name": f"Supplier {i}",
                "website": f"https://supplier{i}.com",
                "category": keyword,
                "quality_score": 75 + (i * 2),
            }
            for i in range(min(limit, 10))
        ]

        task_storage[task_id]["progress"] = 75
        task_storage[task_id]["message"] = "Saving to database..."

        # Save to database
        db = next(get_db())
        try:
            saved_count = 0
            for supplier_data in suppliers:
                supplier = Supplier(**supplier_data)
                db.add(supplier)
                saved_count += 1
            db.commit()

            task_storage[task_id] = {
                "status": "completed",
                "progress": 100,
                "message": f"Successfully scraped {saved_count} suppliers",
                "result": {"count": saved_count, "suppliers": suppliers},
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in deep scrape task {task_id}: {e}")
        task_storage[task_id] = {
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}",
            "error": str(e),
        }


@router.post("/deep-scrape")
async def deep_scrape_suppliers(
    keyword: str,
    limit: int = 50,
    enrich_contacts: bool = True,
    quality_threshold: int = 60,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Enhanced supplier scraping with quality scoring and contact extraction"""

    # Start async scraping task
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        run_deep_scrape, task_id, keyword, limit, enrich_contacts, quality_threshold
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "check_status_at": f"/api/suppliers/tasks/{task_id}/status",
    }


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a background task"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_storage[task_id]


@router.get("/")
async def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    min_quality_score: float | None = None,
    db: Session = Depends(get_db),
):
    """List suppliers with filtering"""

    query = db.query(Supplier)

    if category:
        query = query.filter(Supplier.category == category)

    if min_quality_score:
        query = query.filter(Supplier.quality_score >= min_quality_score)

    suppliers = query.offset(skip).limit(limit).all()

    return {"suppliers": suppliers, "count": len(suppliers), "skip": skip, "limit": limit}


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get a single supplier by ID"""

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return supplier


@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Delete a supplier"""

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()

    return {"message": "Supplier deleted successfully"}


@router.get("/export/csv")
async def export_suppliers_csv(
    category: str | None = None,
    min_quality_score: float | None = None,
    db: Session = Depends(get_db),
):
    """Export suppliers as CSV"""

    try:
        import io

        import pandas as pd
        from fastapi.responses import StreamingResponse

        query = db.query(Supplier)

        if category:
            query = query.filter(Supplier.category == category)

        if min_quality_score:
            query = query.filter(Supplier.quality_score >= min_quality_score)

        suppliers = query.all()

        # Convert to DataFrame
        data = []
        for supplier in suppliers:
            supplier_dict = {
                "id": supplier.id,
                "name": supplier.name,
                "website": supplier.website,
                "category": supplier.category,
                "rating": supplier.rating,
                "quality_score": supplier.quality_score,
                "city": supplier.city,
                "country": supplier.country,
                "emails": ", ".join(supplier.emails or []),
                "phones": ", ".join(supplier.phones or []),
            }
            data.append(supplier_dict)

        df = pd.DataFrame(data)

        # Create CSV stream
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=suppliers.csv"},
        )

    except Exception as e:
        logger.error(f"Error exporting suppliers: {e}")
        raise HTTPException(status_code=500, detail="Export failed") from e
