import os
import signal
import time

from celery import Celery

from .sentiment_model import model
from .db import SessionLocal
from .models import Prediction
from .logger import logger

# Асинхронная очередь
celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
)

shutdown_requested = False


def _handle_sigterm(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    logger.info("Worker received SIGTERM, graceful shutdown requested")


signal.signal(signal.SIGTERM, _handle_sigterm)


# Асинхронная очередь
@celery_app.task(bind=True)
def predict_task(self, text: str):
    task_start = time.perf_counter()
    logger.info("Task received: %s", self.request.id)

    if shutdown_requested:
        logger.warning("Task %s refused because shutdown is in progress", self.request.id)
        raise RuntimeError("Worker is shutting down")

    logger.info("Inference start: %s", self.request.id)
    sentiment = model.generate(text[:1500])
    logger.info("Inference end: %s", self.request.id)

    db = SessionLocal()
    try:
        db.add(Prediction(text=text, sentiment=sentiment))
        db.commit()
        logger.info("DB save completed: %s", self.request.id)
    finally:
        db.close()

    total_ms = (time.perf_counter() - task_start) * 1000
    logger.info("Task %s completed in %.2f ms", self.request.id, total_ms)

    return {"sentiment": sentiment}