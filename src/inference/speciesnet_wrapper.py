from speciesnet import SpeciesNet, DEFAULT_MODEL
from PIL import Image
import io
import tempfile
import os
import uuid
from typing import Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

class SpeciesNetWrapper:
    def __init__(self, region: str = "AUS"):
        self.region = region  # specific to country code, e.g., 'AUS'
        self.model = None

    def initialize(self):
        """
        Initializes the SpeciesNet model using the default model.
        """
        logger.info(f"Initializing SpeciesNet with model: {DEFAULT_MODEL}")
        # Initialize with the default model. 
        # components="all" implies detector + classifier + ensemble
        self.model = SpeciesNet(model_name=DEFAULT_MODEL)

    def predict(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Runs prediction on the image data using SpeciesNet.
        """
        if not self.model:
            self.initialize()

        temp_path = None
        try:
            # SpeciesNet library requires a filepath.
            # Create a unique temp file.
            filename = f"{uuid.uuid4()}.jpg"
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            
            with open(temp_path, "wb") as f:
                f.write(image_data)
            
            # Predict using the file path
            # country should be ISO 3166-1 alpha-3 (e.g. 'AUS')
            logger.debug(f"Running SpeciesNet prediction on {temp_path} with country={self.region}")
            
            # The predict method returns a dict: {'predictions': [ {result_for_file_1}, ... ]}
            start_t = time.perf_counter()
            result = self.model.predict(
                filepaths=[temp_path],
                country=self.region
            )
            end_t = time.perf_counter()
            logger.debug(f"SpeciesNet internal model.predict took {(end_t - start_t)*1000:.2f}ms")

            if not result or "predictions" not in result or not result["predictions"]:
                return []
            
            # Extract the single result
            prediction = result["predictions"][0]
            
            # Parse the output to matching CodeProject.AI format
            mapped_predictions = []
            
            logger.debug(f"SpeciesNet raw prediction keys: {prediction.keys()}")

            # Check for classifications (species level)
            classifications = prediction.get("classifications", {})
            classes = classifications.get("classes", [])
            scores = classifications.get("scores", [])
            
            # Check for detections (bboxes)
            # 'detections' key usually contains a list of dicts directly
            detections = prediction.get("detections", [])
            
            # If we have species classifications, use the top one
            if classes and scores:
                top_label = classes[0]
                top_score = scores[0]
                
                # Use the first detection box if available, otherwise full image
                # CodeProject EXPECTS a bounding box.
                bbox = {"x_min": 0, "y_min": 0, "x_max": 0, "y_max": 0} # Default
                
                if detections:
                    logger.debug(f"SpeciesNet detections list: {detections}")
                    d = detections[0]
                    if "bbox" in d:
                        b = d["bbox"]
                        if isinstance(b, list) and len(b) >= 4:
                             # SpeciesNet format appears to be [x_norm, y_norm, w_norm, h_norm]
                             # Based on log analysis: 
                             # x=0.83 (3215/3840), y=0.54 (1187/2160), w=0.07 (285/3840), h=0.12 (272/2160)
                             
                             norm_x, norm_y, norm_w, norm_h = b[0], b[1], b[2], b[3]
                             
                             # Get image dimensions to scale up
                             try:
                                 with Image.open(io.BytesIO(image_data)) as img:
                                     width, height = img.size
                                 
                                 # Convert to absolute pixels
                                 x_min = int(norm_x * width)
                                 y_min = int(norm_y * height)
                                 x_max = int((norm_x + norm_w) * width)
                                 y_max = int((norm_y + norm_h) * height)
                                 
                                 bbox = {
                                     "y_min": y_min, 
                                     "x_min": x_min, 
                                     "y_max": y_max, 
                                     "x_max": x_max
                                 }
                             except Exception as e:
                                 logger.error(f"Failed to calculate absolute bbox coordinates: {e}")
                                 pass

                mapped_predictions.append({
                    "label": top_label,
                    "confidence": float(top_score),
                    "y_min": bbox["y_min"], 
                    "x_min": bbox["x_min"], 
                    "y_max": bbox["y_max"], 
                    "x_max": bbox["x_max"]
                })
            
            return mapped_predictions

        except Exception as e:
            logger.error(f"Error in SpeciesNet prediction: {e}", exc_info=True)
            return []
        finally:
            # Cleanup
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
