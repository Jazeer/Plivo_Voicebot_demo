# backend/plivo_client.py
import httpx
import base64
from backend.utils import logger


class PlivoClient:
    """
    Minimal Plivo REST client used only for:
      - delete_streams
      - transfer_call
    """

    def __init__(self, auth_id: str, auth_token: str):
        self.auth_id = auth_id
        self.auth_token = auth_token

        token = f"{auth_id}:{auth_token}"
        self.auth_header = {
            "Authorization": "Basic " + base64.b64encode(token.encode()).decode()
        }

        self.base = f"https://api.plivo.com/v1/Account/{auth_id}"

    # -----------------------------------------------------------
    # Delete all active streams on a call
    # -----------------------------------------------------------
    async def delete_streams(self, call_uuid: str):
        url = f"{self.base}/Call/{call_uuid}/Stream/"
        logger.info(f"[Plivo] DELETE streams → {url}")

        async with httpx.AsyncClient() as client:
            r = await client.delete(url, headers=self.auth_header, timeout=10)

        if r.status_code not in (200, 204):
            logger.error(f"[Plivo] delete_streams failed {r.status_code} {r.text}")
            raise Exception("Stream delete failed")

        logger.info("[Plivo] Streams deleted successfully")

    # -----------------------------------------------------------
    # Transfer (Cold or Warm) to Agent
    # -----------------------------------------------------------
    async def transfer_call(self, call_uuid: str, agent_number: str, aleg_url: str):
        """
        Cold Transfer uses:
            aleg_url = https://host/forward-agent

        Warm Transfer uses:
            aleg_url = https://host/forward-agent-warm
        """

        url = f"{self.base}/Call/{call_uuid}/"
        logger.info(f"[Plivo] TRANSFER call → {url}")

        payload = {
            "legs": "aleg",
            "aleg_url": aleg_url,
            "aleg_method": "GET"
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=self.auth_header, timeout=10)

        if r.status_code not in (200, 202):
            logger.error(f"[Plivo] Transfer failed {r.status_code}: {r.text}")
            raise Exception("Transfer failed")

        logger.info("[Plivo] Transfer accepted successfully")
