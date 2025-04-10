import sys
import os
import asyncio
import time

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def run_engine(duration=60):
    from src.ai_trading_framework.main_runtime import main
    task = asyncio.create_task(main())
    print(f"[TEST] Running unstoppable engine for {duration} seconds...")
    await asyncio.sleep(duration)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("[TEST] Engine stopped after timeout.")

def test_unstoppable_engine():
    start = time.time()
    try:
        asyncio.run(run_engine())
    except Exception as e:
        print(f"[TEST ERROR] {e}")
    end = time.time()
    print(f"[TEST] Completed in {end - start:.2f} seconds.")

if __name__ == "__main__":
    test_unstoppable_engine()