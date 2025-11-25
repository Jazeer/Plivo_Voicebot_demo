# backend/utils.py

import logging
import sys
from datetime import datetime

# ------------------------------------------------------------
# Logger configuration
# ------------------------------------------------------------
logger = logging.getLogger("plivo_demo")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(fmt)

if not logger.handlers:
    logger.addHandler(handler)


# ------------------------------------------------------------
# Utility helper (optional logging)
# ------------------------------------------------------------
def session_log(session_id: str, data: dict):
    """
    Store session logs for debugging (extend later if needed).
    Currently prints timestamped JSON to console.
    """
    logger.info(f"[session={session_id}] {data}")
        