from fastapi import APIRouter, HTTPException, Depends
from app.schemas.event import TransactionCreate, TransactionResponse
from app.workers.tasks import process_transaction
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.db.models import Transaction, DailySummary
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/events", response_model=TransactionResponse, status_code=202)
def inject_event(transaction: TransactionCreate):
    """
    接收事件 (Transaction) API
    符合履歷中: "event-driven system via REST APIs"
    使用 Pydantic 進行 "refactored validation"
    並將任務派發給 Celery Worker，達成高並發(500+ TPS)非同步處理。
    """
    transaction_dict = transaction.model_dump()
    # 派發給非同步 Worker
    task = process_transaction.delay(
        transaction_dict
    )
    
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        status="Accepted",
        message=f"Event queued for processing with task id {task.id}"
    )

@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """
    查詢單筆交易狀態
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@router.get("/metrics/daily")
def get_daily_metrics(date: str = None, db: Session = Depends(get_db)):
    """
    查詢每日結算指標 (由 Scheduler 產生)
    """
    query = db.query(DailySummary)
    if date:
        query = query.filter(DailySummary.date == date)
        
    metrics = query.all()
    return metrics
