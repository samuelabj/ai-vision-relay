from fastapi import FastAPI, UploadFile, File
from contextlib import asynccontextmanager
from src.config import settings
from src.proxy import DetectionProxy
from src.clients.blue_onyx import BlueOnyxClient
from src.inference.speciesnet_wrapper import SpeciesNetWrapper
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BlueIrisAiProxy")

# Global instances
proxy: DetectionProxy = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SpeciesNet AI Proxy...")
    
    blue_onyx = BlueOnyxClient(base_url=settings.BLUE_ONYX_URL)
    
    speciesnet = SpeciesNetWrapper(region=settings.SPECIESNET_REGION)
    # Warm up / Load model
    speciesnet.initialize()
    
    global proxy
    proxy = DetectionProxy(blue_onyx, speciesnet)
    
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.post("/v1/vision/detection")
async def detect(image: UploadFile = File(...)):
    if not proxy:
        return {"success": False, "error": "Service not initialized"}
    
    image_data = await image.read()
    result = await proxy.process_image(image_data)
    return result

if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=False)
