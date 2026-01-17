from src.config import settings
from src.clients.blue_onyx import BlueOnyxClient
from src.inference.speciesnet_wrapper import SpeciesNetWrapper
import logging

logger = logging.getLogger(__name__)

class DetectionProxy:
    def __init__(self, blue_onyx_client: BlueOnyxClient, speciesnet: SpeciesNetWrapper):
        self.blue_onyx = blue_onyx_client
        self.speciesnet = speciesnet

    async def process_image(self, image_data: bytes):
        # 1. Send to Blue Onyx
        bo_response = await self.blue_onyx.detect(image_data)
        
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
            logger.info("Running SpeciesNet...")
            sn_predictions = self.speciesnet.predict(image_data)
            if sn_predictions:
                logger.info(f"SpeciesNet found {len(sn_predictions)} predictions.")
                # Strategy: Append specialized predictions. 
                # Blue Iris will see all of them.
                final_predictions.extend(sn_predictions)
            else:
                logger.info("SpeciesNet found nothing.")
        
        return {
            "success": True, 
            "predictions": final_predictions,
            "message": "Processed by BlueIrisAiProxyServer",
            "count": len(final_predictions)
        }
