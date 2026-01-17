import httpx
from typing import Dict, Any, Optional
import os

class BlueOnyxClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.detect_url = f"{self.base_url}/v1/vision/detection"

    async def detect(self, image_data: bytes) -> Dict[str, Any]:
        """
        Sends image to Blue Onyx for detection.
        Returns the raw JSON response from Blue Onyx (CodeProject.AI format).
        """
        try:
            files = {'image': ('image.jpg', image_data, 'image/jpeg')}
            async with httpx.AsyncClient() as client:
                response = await client.post(self.detect_url, files=files, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # If Blue Onyx fails, we might still want to try SpeciesNet?
            # For now, let's log and return a failure-like response or re-raise.
            # Returning an empty success=False response allows the calling logic to decide.
            print(f"Error calling Blue Onyx: {e}")
            return {"success": False, "predictions": [], "error": str(e)}
