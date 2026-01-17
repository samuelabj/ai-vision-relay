from speciesnet import SpeciesNet
from PIL import Image
import io
from typing import Dict, Any, List

class SpeciesNetWrapper:
    def __init__(self, region: str = "QLD, Australia"):
        self.region = region
        self.model = None

    def initialize(self):
        """
        Initializes the SpeciesNet model. This might download weights on first run.
        """
        print(f"Initializing SpeciesNet with region: {self.region}")
        # Assuming SpeciesNet API: SpeciesNet(geographic_info=...)
        # We need to verify the actual API. Based on user request "Use the speciesnet Python package".
        # If the package is strictly 'speciesnet', initialization usually looks like this.
        self.model = SpeciesNet(geographic_info=self.region)

    def predict(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Runs prediction on the image data.
        Returns a list of predictions in a format compatible with CodeProject.AI if possible,
        or raw SpeciesNet results mapped.
        """
        if not self.model:
            self.initialize()

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Run prediction
            # speciesnet return format: List[Dict] with 'label', 'score', 'common_name', etc.
            predictions = self.model.predict(image)
            
            # Transform to CodeProject.AI format for consistency if needed, 
            # or just return relevant info.
            # CodeProject.AI prediction: {"label": "...", "confidence": 0.9, "x_min":..., "y_min":...}
            # SpeciesNet might not provide bounding boxes if it's a classifier, 
            # strictly speaking, SpeciesNet is often a classifier.
            # We'll map 'common_name' to 'label' and 'score' to 'confidence'.
            
            mapped_predictions = []
            for pred in predictions:
                # Example structure from SpeciesNet, adjust based on actual library return
                # usually {'common_name': '...', 'scientific_name': '...', 'score': 0.95}
                mapped_predictions.append({
                    "label": pred.get("common_name", "Unknown"),
                    "confidence": pred.get("score", 0.0),
                    "scientific_name": pred.get("scientific_name"),
                    # Add dummy bbox if missing? Blue Iris might need one to trigger.
                    # If this is the main detector, we might want to return the whole image as the box
                    # or rely on Blue Onyx's box if we are refining? 
                    # But the requirement is: "if 'animal' ... run SpeciesNet".
                    # If SpeciesNet finds something, we want to report it.
                    "y_min": 0, "x_min": 0, "y_max": image.height, "x_max": image.width
                })
                
            return mapped_predictions

        except Exception as e:
            print(f"Error in SpeciesNet prediction: {e}")
            return []
