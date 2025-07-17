from concurrent.futures import ThreadPoolExecutor

from src.core import logger, settings

"""
Thread pool executor for background processing.

This module provides a reusable ThreadPoolExecutor instance for CPU-bound or
blocking I/O tasks, with controlled concurrency and cleanup support.
"""
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

def cleanup_executor():
    """
    Gracefully shuts down the global thread pool executor.

    This function should be called during application shutdown
    to ensure all threads complete their work and resources are released.
    """
    try:
        logger.info("Shutting down thread pool executor...")
        executor.shutdown(wait=True)
        logger.info("Thread pool executor successfully shut down.")
    except Exception as e:
        logger.exception(f"Error during executor shutdown: {e}")