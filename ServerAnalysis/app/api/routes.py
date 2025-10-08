from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from pydantic import BaseModel

from app.local_database.connection import get_db
from app.services.database_service import DatabaseService
from app.services.orchestration_service import OrchestrationService
from app.core.tasks.user_analysis_tasks import run_daily_analysis_task

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    date: str

# Endpoint to start a daily-analysis
@router.post("/analysis/daily")
async def start_daily_analysis(request: AnalysisRequest, db = Depends(get_db)) -> Dict[str, Any]:
    try:
        db_service = DatabaseService(db)
        orchestration_service = OrchestrationService(db_service)

        result = orchestration_service.run_daily_analysis(request.date)
    except Exception as e:
        logger.error(f"Error starting daily analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "analysis started", "date": request.date, "result": result}

# NOTE: This is to trigger the task for daily analysis (like the scheduler will do)
# ONLY FOR TESTING
# @router.post("/analysis/trigger-daily-task")
# async def trigger_daily_analysis_task() -> Dict[str, Any]:
#     """
#     Manually trigger the scheduled daily analysis task.
#     This will run the task asynchronously via Celery.
#     """
#     try:
#         # Trigger the task asynchronously
#         job = run_daily_analysis_task.delay()
        
#         return {
#             "status": "Task triggered successfully",
#             "job_id": job.id,
#             "message": "The daily analysis task has been queued and will run shortly"
#         }
#     except Exception as e:
#         logger.error(f"Error triggering daily analysis task: {e}")
#         raise HTTPException(status_code=500, detail=str(e))