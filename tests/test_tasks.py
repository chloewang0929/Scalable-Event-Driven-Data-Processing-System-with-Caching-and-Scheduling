import json
from app.workers.tasks import process_transaction, transform_amount, is_suspicious
from app.db.models import Transaction
from app.db.session import SessionLocal

def test_transform_amount():
    # 測試內部演算法
    assert transform_amount(100, 'EUR') == 110.0
    assert transform_amount(100, 'TWD') == 3.2

def test_is_suspicious():
    assert is_suspicious(5000) == False
    assert is_suspicious(15000) == True

def test_process_transaction_new(mock_redis):
    # 模擬 Mock Session
    from tests.conftest import TestingSessionLocal
    from unittest.mock import patch
    
    with patch('app.workers.tasks.SessionLocal', TestingSessionLocal):
        tx_data = {
            "transaction_id": "tx-999",
            "user_id": "user-999",
            "amount": 100,
            "currency": "EUR"
        }
        # 第一次處理
        result = process_transaction(tx_data)
        assert result['status'] == 'processed'
        assert result['converted_amount'] == 110.0
        
        # 驗證有寫入 DB
        db = TestingSessionLocal()
        tx = db.query(Transaction).filter(Transaction.transaction_id == "tx-999").first()
        assert tx is not None
        assert tx.converted_amount == 110.0
        db.close()
        
        # 驗證有寫入 Redis 快取
        cached_raw = mock_redis.get("tx_cache:tx-999")
        assert cached_raw is not None
        cached_data = json.loads(cached_raw)
        assert cached_data['converted_amount'] == 110.0

def test_process_transaction_cached(mock_redis):
    # 手動塞入 Redis 快取模擬 "減少 redundant computations"
    cache_key = "tx_cache:tx-888"
    mock_result = {
        "transaction_id": "tx-888",
        "converted_amount": 999.0,
        "is_fraudulent": False,
        "status": "processed"
    }
    mock_redis.set(cache_key, json.dumps(mock_result))
    
    tx_data = {
        "transaction_id": "tx-888",
        "user_id": "user-888",
        "amount": 900,
        "currency": "EUR"
    }
    # 執行任務，此時應該直接命中快取，不走 DB 或轉換演算法
    result = process_transaction(tx_data)
    
    assert result['converted_amount'] == 999.0 # 如果重新算會是 990，回傳 999 證明直接拿快取
