import asyncio

async def with_timeout_retry(fn, *, timeout_s=8, retries=1):
    """Bound external tool latency and retry transient timeout/connection failures."""
    last = None
    for attempt in range(retries + 1):
        try:
            return await asyncio.wait_for(fn(), timeout=timeout_s)
        except (TimeoutError, ConnectionError) as exc:
            last = exc
            if attempt < retries:
                await asyncio.sleep(0.1 * (2 ** attempt))
    raise last
