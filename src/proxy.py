from src.config import settings
from src.clients.blue_onyx import BlueOnyxClient
from src.inference.speciesnet_wrapper import SpeciesNetWrapper
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

class DetectionProxy:
    def __init__(self, blue_onyx_client: BlueOnyxClient, speciesnet: SpeciesNetWrapper):
        self.blue_onyx = blue_onyx_client
        self.speciesnet = speciesnet
        self.processing_lock = asyncio.Lock()

    async def process_image(self, image_data: bytes):
        logger.debug(f"Processing image of size: {len(image_data)} bytes")
        
        # 1. Send to Blue Onyx
        start_time_bo = time.perf_counter()
        bo_response = await self.blue_onyx.detect(image_data)
        end_time_bo = time.perf_counter()
        duration_bo = (end_time_bo - start_time_bo) * 1000
        logger.info(f"Blue Onyx inference took {duration_bo:.2f}ms")
        logger.debug(f"Blue Onyx raw response: {bo_response}")
        
        should_run_speciesnet = False
        bo_predictions = bo_response.get("predictions", [])
        
        # Logic: If empty predictions OR specific labels found
        if not bo_predictions:
            logger.info("Blue Onyx returned no predictions. Triggering SpeciesNet.")
            should_run_speciesnet = True
        else:
            for pred in bo_predictions:
                label = pred.get("label", "").lower()
                if label in [t.lower() for t in settings.TRIGGER_LABELS]:
                    logger.info(f"Blue Onyx detected trigger '{label}'. Triggering SpeciesNet.")
                    should_run_speciesnet = True
                    break
        
        final_predictions = bo_predictions
        
        # 2. Run SpeciesNet if triggered
        if should_run_speciesnet:
            logger.info("Waiting for SpeciesNet lock...")
            async with self.processing_lock:
                logger.info("Acquired SpeciesNet lock. Running inference...")
                start_time_sn = time.perf_counter()
                
                # Run the blocking prediction in a separate thread to keep the event loop responsive
                sn_predictions = await asyncio.to_thread(self.speciesnet.predict, image_data)
                
                end_time_sn = time.perf_counter()
                duration_sn = (end_time_sn - start_time_sn) * 1000
                logger.info(f"SpeciesNet inference took {duration_sn:.2f}ms")
            
            logger.debug(f"SpeciesNet raw predictions: {sn_predictions}")
            
            # Filter blank predictions and check confidence
            valid_sn_predictions = []
            if sn_predictions:
                for pred in sn_predictions:
                    # 1. Check Blank Label
                    if pred.get("label") == settings.SPECIESNET_BLANK_LABEL:
                        logger.debug("Ignoring SpeciesNet blank prediction.")
                        continue
                    
                    # 2. Check Confidence Threshold
                    score = pred.get("score", 0.0)
                    if score < settings.SPECIESNET_CONFIDENCE_THRESHOLD:
                        logger.debug(f"Ignoring SpeciesNet prediction '{pred.get('label')}' with low confidence: {score:.2f} < {settings.SPECIESNET_CONFIDENCE_THRESHOLD}")
                        continue
                        
                    valid_sn_predictions.append(pred)
            
            if valid_sn_predictions:
                logger.info(f"SpeciesNet found {len(valid_sn_predictions)} predictions.")
                # Strategy: Append specialized predictions. 
                # Blue Iris will see all of them.
                final_predictions.extend(valid_sn_predictions)
            else:
                logger.info("SpeciesNet found nothing (or filtered all predictions).")
        
        return {
            "success": True, 
            "predictions": final_predictions,
            "message": "Processed by AI-Vision-Relay",
            "count": len(final_predictions)
        }
