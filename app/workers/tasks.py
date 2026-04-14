from celery.utils.log import get_task_logger
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Transaction
from datetime import datetime
import json
import redis
import hashlib
from app.core.config import settings

logger = get_task_logger(__name__)

# 直接使用 Redis Client 處理自訂快取邏輯
redis_client = redis.from_url(settings.REDIS_URL)

# 模擬匯率轉換 (實際場景可能打外部 API)
EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 1.1,
    'GBP': 1.25,
    'JPY': 0.0068,
    'TWD': 0.032
}

def transform_amount(amount: float, currency: str) -> float:
    # 這裡代表耗時的演算法或轉換邏輯
    rate = EXCHANGE_RATES.get(currency.upper(), 1.0)
    return round(amount * rate, 2)

def is_suspicious(amount: float) -> bool:
    # 簡單的防詐騙檢查演算法 (金額超過 10000 標記為可疑)
    return amount > 10000

@celery_app.task(bind=True, max_retries=3)
def process_transaction(self, transaction_data: dict):
    transaction_id = transaction_data.get('transaction_id')
    amount = transaction_data.get('amount')
    currency = transaction_data.get('currency')
    user_id = transaction_data.get('user_id')

    # 【快取機制】使用 Redis Hash 確保同一筆交易不會被重複計算
    # 模擬 履歷中提到的 "reducing redundant computations by 30%"
    cache_key = f"tx_cache:{transaction_id}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.info(f"Transaction {transaction_id} already processed (Cache Hit). Skipping redundant computation.")
        return json.loads(cached_result)

    try:
        # 開始耗時計算: 轉換匯率、防詐驗證
        converted_amt = transform_amount(amount, currency)
        suspicious = is_suspicious(converted_amt)
        
        # 準備存回資料庫
        db = SessionLocal()
        try:
            # 檢查 DB 是否已經存在 (避免 Celery 重複發送問題)
            existing = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
            if not existing:
                new_tx = Transaction(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    amount=amount,
                    currency=currency,
                    converted_amount=converted_amt,
                    is_fraudulent=suspicious,
                    processed_at=datetime.utcnow()
                )
                db.add(new_tx)
                db.commit()
                logger.info(f"Transaction {transaction_id} saved to DB.")
        finally:
            db.close()

        # 計算結果寫入 Redis 快取，設定過期時間 24h
        result = {
            "transaction_id": transaction_id,
            "converted_amount": converted_amt,
            "is_fraudulent": suspicious,
            "status": "processed"
        }
        redis_client.setex(cache_key, 86400, json.dumps(result))
        
        return result

    except Exception as exc:
        logger.error(f"Error processing transaction {transaction_id}: {exc}")
        self.retry(exc=exc, countdown=5)
