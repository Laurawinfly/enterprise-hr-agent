import json
import logging
from app.security.redaction import redact

logger = logging.getLogger("audit")

def audit(event, **fields):
    """Emit a redacted structured audit event. Production should persist/ship these logs."""
    safe = redact({"event": event, **fields})
    logger.info(json.dumps(safe, ensure_ascii=False))
    return safe
