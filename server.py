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
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("Server")
    logger.info("Starting AI-Vision-Relay Service...")
    
    try:
        # log_config=None tells uvicorn to use the existing logging config (from basicConfig)
        uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, log_level=settings.LOG_LEVEL.lower(), reload=False, log_config=None)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
