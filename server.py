import uvicorn
from src.config import settings
import logging
import sys
import os

# Ensure src is in pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Configure logging for the service
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("service.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("Server")
    logger.info("Starting BlueIrisAiProxyServer Service...")
    
    try:
        uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, log_level="info", reload=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
