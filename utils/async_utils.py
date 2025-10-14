import asyncio
from utils.logger import logger

async def gather_with_timeout(tasks, timeout: float):
    """Run tasks concurrently with timeout handling."""
    try:
        return await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timeout reached while gathering agent responses.")
        return [{"agent": "unknown", "ok": False, "data": {"error": "timeout"}}]
