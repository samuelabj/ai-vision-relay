import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.proxy import DetectionProxy
from src.clients.blue_onyx import BlueOnyxClient
from src.inference.speciesnet_wrapper import SpeciesNetWrapper

class TestDetectionProxy(unittest.TestCase):
    def setUp(self):
        self.blue_onyx = MagicMock(spec=BlueOnyxClient)
        self.speciesnet = MagicMock(spec=SpeciesNetWrapper)
        self.proxy = DetectionProxy(self.blue_onyx, self.speciesnet)
        self.image_data = b"fake_image_bytes"

    def test_blue_onyx_no_trigger(self):
        # Setup: Blue Onyx finds a 'car' (not in trigger list)
        self.blue_onyx.detect = AsyncMock(return_value={
            "success": True, 
            "predictions": [{"label": "car", "confidence": 0.9}]
        })
        
        # Action
        result = asyncio.run(self.proxy.process_image(self.image_data))
        
        # Assert
        self.speciesnet.predict.assert_not_called()
        self.assertEqual(len(result["predictions"]), 1)
        self.assertEqual(result["predictions"][0]["label"], "car")

    def test_blue_onyx_trigger(self):
        # Setup: Blue Onyx finds a 'cat' (trigger)
        self.blue_onyx.detect = AsyncMock(return_value={
            "success": True, 
            "predictions": [{"label": "cat", "confidence": 0.8}]
        })
        self.speciesnet.predict.return_value = [
            {"label": "Felis catus", "confidence": 0.95}
        ]
        
        # Action
        result = asyncio.run(self.proxy.process_image(self.image_data))
        
        # Assert
        self.speciesnet.predict.assert_called_once()
        self.assertEqual(len(result["predictions"]), 2) # cat + Felis catus

    def test_blue_onyx_empty_response(self):
        # Setup: Blue Onyx finds nothing (trigger condition: empty)
        self.blue_onyx.detect = AsyncMock(return_value={
            "success": True, 
            "predictions": []
        })
        self.speciesnet.predict.return_value = [
            {"label": "Possum", "confidence": 0.9}
        ]
        
        # Action
        result = asyncio.run(self.proxy.process_image(self.image_data))
        
        # Assert
        self.speciesnet.predict.assert_called_once()
        self.assertEqual(len(result["predictions"]), 1)
        self.assertEqual(result["predictions"][0]["label"], "Possum")

if __name__ == "__main__":
    unittest.main()
