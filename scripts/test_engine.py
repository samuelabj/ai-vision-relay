import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clients.blue_onyx import BlueOnyxClient
from src.inference.speciesnet_wrapper import SpeciesNetWrapper
from src.engine import DetectionEngine
from src.config import settings

class TestDetectionEngine(unittest.TestCase):
    def setUp(self):
        self.blue_onyx = MagicMock(spec=BlueOnyxClient)
        self.speciesnet = MagicMock(spec=SpeciesNetWrapper)
        # Mock settings for the engine
        settings.TRIGGER_LABELS = ["cat", "empty"]
        self.engine = DetectionEngine(self.blue_onyx, self.speciesnet)
        self.image_data = b"fake_image_bytes"

    def test_blue_onyx_no_trigger(self):
        # Setup: Blue Onyx finds a 'car' (not in trigger list)
        self.blue_onyx.detect = AsyncMock(return_value={
            "success": True, 
            "predictions": [{"label": "car", "confidence": 0.9}]
        })
        
        # Action
        result = asyncio.run(self.engine.process_image(self.image_data))
        
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
        result = asyncio.run(self.engine.process_image(self.image_data))
        
        # Assert
        self.speciesnet.predict.assert_called_once()
        self.assertEqual(len(result["predictions"]), 3) # cat + Felis catus + generic animal

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
        result = asyncio.run(self.engine.process_image(self.image_data))
        
        # Assert
        self.speciesnet.predict.assert_called_once()
        self.assertEqual(len(result["predictions"]), 2) # Possum + generic animal
        self.assertEqual(result["predictions"][0]["label"], "Possum")

    def test_speciesnet_blank_filtering(self):
        # Setup: Blue Onyx finds nothing -> Trigger SpeciesNet
        self.blue_onyx.detect = AsyncMock(return_value={"success": True, "predictions": []})
        
        # SpeciesNet returns a blank prediction with high confidence
        self.speciesnet.predict.return_value = [
            {"label": settings.SPECIESNET_BLANK_LABEL, "confidence": 0.99}, # The raw label string from settings
            {"label": "Just Blank", "confidence": 0.95} # Should also check cleaned logic if we want, but let's test the raw match first
        ]
        # Wait, my logic in engine.py checks:
        # if raw_label == settings.SPECIESNET_BLANK_LABEL or clean_label.lower() == "blank":
        
        # Let's test BOTH cases in one go or separate. 
        # Case 1: Exact Match of Config String
        
        # Action
        result = asyncio.run(self.engine.process_image(self.image_data))
        
        # Assert: Should be empty because "Just Blank" cleans to "blank" (if format is "uuid;...;blank") OR if it's just "Just Blank" -> "Just Blank" != "blank".
        # Wait, split(";")[-1]. 
        # "Just Blank".split(";")[-1] is "Just Blank". lower() is "just blank". != "blank".
        # So "Just Blank" should be KEPT.
        # But the first one should be FILTERED.
        
        # Let's adjust the test data to be precise.
        self.speciesnet.predict.return_value = [
            {"label": settings.SPECIESNET_BLANK_LABEL, "confidence": 0.99}, # Should be filtered (Exact Match)
            {"label": "some-uuid;;;;;;blank", "confidence": 0.98}, # Should be filtered (Cleaned Match)
            {"label": "Real Animal", "confidence": 0.95} # Should be Kept
        ]
        
        result = asyncio.run(self.engine.process_image(self.image_data))
        
        self.assertEqual(len(result["predictions"]), 2) # Real Animal + generic animal
        # The first two should be ignored.
        self.assertEqual(result["predictions"][0]["label"], "Real Animal")

if __name__ == "__main__":
    unittest.main()
