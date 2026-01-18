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
        start_time_total = time.perf_counter()
        logger.info(f"Received detection request for image of size: {len(image_data)} bytes")
        # ... (rest of logic) ...

        # ... (constructing summary msg) ...
        # [Wait, I need to inject start_time at top of function first]
        # I'll do this in two chunks using multi_replace_file_content for safety.

        logger.debug(f"Processing image of size: {len(image_data)} bytes")
        
        # 1. Send to Blue Onyx
        start_time_bo = time.perf_counter()
        bo_response = await self.blue_onyx.detect(image_data)
        end_time_bo = time.perf_counter()
        duration_bo = (end_time_bo - start_time_bo) * 1000
        logger.debug(f"Blue Onyx inference took {duration_bo:.2f}ms")
        logger.debug(f"Blue Onyx raw response: {bo_response}")
        
        should_run_speciesnet = False
        bo_predictions = bo_response.get("predictions", [])
        
        # Logic: If empty predictions OR specific labels found
        if not bo_predictions:
            logger.debug("Blue Onyx returned no predictions. Triggering SpeciesNet.")
            should_run_speciesnet = True
        else:
            for pred in bo_predictions:
                label = pred.get("label", "").lower()
                if label in [t.lower() for t in settings.TRIGGER_LABELS]:
                    logger.debug(f"Blue Onyx detected trigger '{label}'. Triggering SpeciesNet.")
                    should_run_speciesnet = True
                    break
        
        final_predictions = list(bo_predictions)
        
        # 2. Run SpeciesNet if triggered
        if should_run_speciesnet:
            logger.debug("Waiting for SpeciesNet lock...")
            async with self.processing_lock:
                logger.debug("Acquired SpeciesNet lock. Running inference...")
                start_time_sn = time.perf_counter()
                
                # Run the blocking prediction in a separate thread to keep the event loop responsive
                sn_predictions = await asyncio.to_thread(self.speciesnet.predict, image_data)
                
                end_time_sn = time.perf_counter()
                duration_sn = (end_time_sn - start_time_sn) * 1000
                logger.debug(f"SpeciesNet inference took {duration_sn:.2f}ms")
            
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
                    score = pred.get("confidence", pred.get("score", 0.0))
                    if score < settings.SPECIESNET_CONFIDENCE_THRESHOLD:
                        logger.debug(f"Ignoring SpeciesNet prediction '{pred.get('label')}' with low confidence: {score:.2f} < {settings.SPECIESNET_CONFIDENCE_THRESHOLD}")
                        continue
                        
                    valid_sn_predictions.append(pred)
            
            if valid_sn_predictions:
                logger.debug(f"SpeciesNet found {len(valid_sn_predictions)} predictions.")
                # Strategy: Append specialized predictions. 
                # Blue Iris will see all of them.
                final_predictions.extend(valid_sn_predictions)
                
                # Also add ONE generic "animal" label if any SpeciesNet detection exists.
                # Use the highest confidence score found.
                if valid_sn_predictions:
                    best_pred = max(valid_sn_predictions, key=lambda p: p.get("confidence", p.get("score", 0.0)))
                    generic_pred = best_pred.copy()
                    generic_pred["label"] = "animal"
                    final_predictions.append(generic_pred)
            else:
                logger.debug("SpeciesNet found nothing (or filtered all predictions).")

        # Consolidated Summary Log (INFO)
        # This ensures every request produces one high-level INFO log
        
        # Collect labels for logging
        def fmt_pred(p):
            label = p.get("label", "unknown")
            score = p.get("confidence", p.get("score", 0.0))
            return f"{label} ({score:.2f})"

        bo_labels = [fmt_pred(p) for p in bo_predictions]
        # Only check valid_sn_predictions if we actually ran SpeciesNet *and* found something
        sn_labels = []
        if should_run_speciesnet and 'valid_sn_predictions' in locals():
            sn_labels = [fmt_pred(p) for p in valid_sn_predictions]

        msg = f"Request processed. Blue Onyx: {len(bo_predictions)} {bo_labels}, SpeciesNet: "
        if should_run_speciesnet:
             # Just show the count of VALID predictions added
             msg += f"{len(sn_labels)} {sn_labels}"
        else:
            msg += "Skipped (No Trigger)"
        
        # Calculate total duration
        end_time_total = time.perf_counter()
        duration_total = end_time_total - start_time_total
        msg += f". Time: {duration_total:.2f}s"
        
        logger.info(msg)
        
        return {
            "success": True, 
            "predictions": final_predictions,
            "message": "Processed by AI-Vision-Relay",
            "count": len(final_predictions)
        }
