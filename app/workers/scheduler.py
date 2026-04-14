from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Transaction, DailySummary
from datetime import datetime, date
from sqlalchemy import func

@celery_app.task
def aggregate_daily():
    """
    此為 Batch Scheduling 負責執行的工作：
    定期將 Transactions 資料彙整並更新至 DailySummary 表格中。
    在履歷中對應：'batch scheduling'
    """
    db = SessionLocal()
    try:
        today_str = date.today().strftime("%Y-%m-%d")

        # 計算今日已處理的交易指標
        result = db.query(
            func.count(Transaction.id).label("total_tx"),
            func.sum(Transaction.converted_amount).label("total_amount"),
            func.sum(func.cast(Transaction.is_fraudulent, func.integer())).label("fraud_tx")
        ).filter(
            func.date(Transaction.created_at) == date.today()
        ).first()

        total_tx = result.total_tx or 0
        total_amount = result.total_amount or 0.0
        fraud_tx = result.fraud_tx or 0

        # Upsert 邏輯
        summary = db.query(DailySummary).filter(DailySummary.date == today_str).first()
        if summary:
            summary.total_transactions = total_tx
            summary.total_amount_usd = total_amount
            summary.fraudulent_transactions = fraud_tx
        else:
            new_summary = DailySummary(
                date=today_str,
                total_transactions=total_tx,
                total_amount_usd=total_amount,
                fraudulent_transactions=fraud_tx
            )
            db.add(new_summary)
            
        db.commit()
    finally:
        db.close()
    return f"Daily summary updated for {today_str}: {total_tx} transactions."
