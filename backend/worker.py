# ============================
# 📁 backend/worker.py
# RQ background worker
# ============================
import os
import sys
import logging
from redis import Redis
from rq import Worker, Queue, Connection
from config import REDIS_URL, RQ_QUEUE_NAME
from logging_setup import init_logging

def main():
    """Start RQ worker for Mini Studio background jobs"""
    
    # Initialize logging
    init_logging("worker")
    logger = logging.getLogger("worker")
    
    logger.info("Starting Mini Studio background worker...")
    logger.info(f"Redis URL: {REDIS_URL}")
    logger.info(f"Queue: {RQ_QUEUE_NAME}")
    
    try:
        # Connect to Redis
        conn = Redis.from_url(REDIS_URL)
        
        # Test connection
        conn.ping()
        logger.info("Connected to Redis successfully")
        
        # Create queue
        queue = Queue(RQ_QUEUE_NAME, connection=conn)
        logger.info(f"Queue '{RQ_QUEUE_NAME}' initialized")
        
        # Start worker
        with Connection(conn):
            worker = Worker([queue])
            logger.info("Worker started. Waiting for jobs...")
            worker.work(with_scheduler=True)
            
    except Exception as e:
        logger.error(f"Worker startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()