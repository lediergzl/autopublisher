import time
import logging

logger = logging.getLogger("autopublisher.audit")
logging.basicConfig(level=logging.INFO)


async def audit_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "%s %s %s %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response
