import uvicorn
from src.config import settings
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os
import asyncio
import threading

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
    # Call default handler for everything else
    loop.default_exception_handler(context)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("Server").critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(1)

def handle_thread_exception(args):
    logging.getLogger("Server").critical(f"Uncaught thread exception in {args.thread.name}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    os._exit(1) # Force exit to prevent zombie process

# Filter for Service Logs (Stdout)
class ServiceFilter(logging.Filter):
    def filter(self, record):
        # Allow warnings/errors OR messages specifically from "Server" logger (startup/shutdown)
        return record.levelno >= logging.WARNING or record.name == "Server"

# Custom Handler to force flushing (fix for delayed logs)
class FlushingFileHandler(TimedRotatingFileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

async def main():
    # 1. Define Formatters
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 2. File Handler (Rotated by Python) - Captures EVERYTHING (INFO+)
    # Use FlushingFileHandler to ensure logs are written immediately
    file_handler = FlushingFileHandler(
        "server.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_handler.setFormatter(formatter)

    # 3. Stream Handler (Console/Service)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    # Logic: Default to Console (Verbose), switch to Service (Quiet) if flag present
    if "--service" in sys.argv:
        # Service Mode: Quiet, filtered (for NSSM)
        stream_handler.setLevel(logging.WARNING)
        stream_handler.addFilter(ServiceFilter())
    else:
        # Console Mode: Verbose (for debugging)
        stream_handler.setLevel(settings.LOG_LEVEL)

    # Configure logging for the service
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        handlers=[file_handler, stream_handler]
    )
    
    logger = logging.getLogger("Server")
    logger = logging.getLogger("Server")
    logger.info("Starting AI-Vision-Relay Service...")
    
    # Register Global Exception Hooks
    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception
    
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
