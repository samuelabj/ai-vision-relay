import uvicorn
from src.config import settings
import logging
import sys
import os
import asyncio

# Ensure src is in pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def asyncio_exception_handler(loop, context):
    # Suppress known benign Windows network errors
    exception = context.get("exception")
    if isinstance(exception, OSError):
        if exception.winerror in [64, 121, 1236]: 
            # 64: Network name no longer available
            # 121: Semaphore timeout period has expired
            # 1236: Network connection aborted by local system
            return
            
    # Also check message string if exception object isn't present
    msg = context.get("message", "")
    if "WinError 64" in msg or "WinError 121" in msg:
        return

    # Call default handler for everything else
    loop.default_exception_handler(context)

async def main():
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
        config = uvicorn.Config("src.main:app", host=settings.HOST, port=settings.PORT, log_level=settings.LOG_LEVEL.lower(), reload=False, log_config=None)
        server = uvicorn.Server(config)
        
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(asyncio_exception_handler)
        
        await server.serve()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
