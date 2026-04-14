import asyncio
import httpx
import time
import random
import uuid

API_URL = "http://localhost:8000/api/v1/events"
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'TWD']

async def send_request(client, tx_id):
    payload = {
        "transaction_id": f"tx-{tx_id}",
        "user_id": f"user-{random.randint(1, 100)}",
        "amount": round(random.uniform(10.0, 5000.0), 2),
        "currency": random.choice(CURRENCIES)
    }
    
    # 模擬 30% 左右的重複請求 (命中 Redis 快取)
    if random.random() < 0.3:
        payload["transaction_id"] = f"tx-{tx_id % 10}" # 故意用前面幾筆

    try:
        response = await client.post(API_URL, json=payload)
        return response.status_code
    except Exception as e:
        return 500

async def main():
    print("🚀 Starting Load Test...")
    print("Creating simulated transactions to reach 500+ TPS...")
    
    # 目標：嘗試在短時間內送出 1000 筆 Request 模擬高並發
    NUM_REQUESTS = 1000
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(NUM_REQUESTS):
            tasks.append(send_request(client, str(uuid.uuid4())[:8] + f"-{i}"))
        
        results = await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time
    
    success = results.count(202)
    tps = NUM_REQUESTS / duration if duration > 0 else 0
    
    print("\n📊 --- Load Test Results ---")
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Successful Requests: {success} ({(success/NUM_REQUESTS)*100}%)")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Requests Per Second (TPS): {tps:.2f} requests/sec")
    
    if tps > 500:
        print("\n✅ Success: Target of 500+ requests per second achieved!")
    else:
        print("\n⚠️ Note: Did not hit 500+ TPS strictly from Python client side.")
        print("To truly benchmark, consider using robust tools like JMeter or loadtest.")

if __name__ == "__main__":
    asyncio.run(main())
