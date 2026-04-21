import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as sql_text

from .db import Base, engine, SessionLocal
from .sentiment_model import model
from .schemas import PredictRequest
from .tasks import predict_task, celery_app
from .models import Prediction

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("API started")
    yield
    logger.info("API stopped gracefully")

app = FastAPI(
    title="AI Sentiment API",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api",
)

# middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} completed in {duration:.3f}s")
    return response

# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# Health Check
@app.get("/health")
def health():
    details = {"api": "ok", "db": "unknown", "model": "ok"}
    overall_ok = True
    try:
         # DB readiness
        db = SessionLocal()
        db.execute(sql_text("SELECT 1"))
        details["db"] = "ok"
    except Exception as e:
        details["db"] = f"error: {str(e)}"
        overall_ok = False
    finally:
        try:
            db.close()
        except:
            pass

    # Model readiness
    try:
        if model is None:
            raise RuntimeError("Model instance is None")

        if not hasattr(model, "model") or model.model is None:
            raise RuntimeError("Loaded classifier is missing")

        if not hasattr(model, "vectorizer") or model.vectorizer is None:
            raise RuntimeError("Loaded vectorizer is missing")

        # Small real inference test
        test_result = model.generate("This is a health check sample")

        if test_result not in {"negative", "neutral", "positive"}:
            raise RuntimeError(f"Unexpected prediction result: {test_result}")

        details["model"] = "ok"
    except Exception as e:
        details["model"] = f"error: {str(e)}"
        overall_ok = False

    if overall_ok:
        return {"status": "ok", **details}

    return JSONResponse(
        status_code=503,
        content={"status": "down", **details},
    )

# Асинхронная очередь
# Task is sent to Celery worker
@app.post("/predict", status_code=202)
def predict(req: PredictRequest):
    task = predict_task.delay(req.text)
    return {"task_id": task.id}

# Асинхронная очередь
# Polling task result(status)
@app.get("/result/{task_id}")
def result(task_id: str):
    result_obj = celery_app.AsyncResult(task_id)

    if result_obj.failed():
        return JSONResponse(status_code=500, content={"status": "failed"})

    if result_obj.ready():
        return {"status": "done", **result_obj.result}

    return {"status": "pending"}

# ORM
@app.get("/history")
def history():
    db = SessionLocal()
    rows = db.query(Prediction).all()
    data = [
        {"id": row.id, "sentiment": row.sentiment}
        for row in rows
    ]
    db.close()
    return data