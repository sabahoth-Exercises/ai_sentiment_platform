import asyncio
import time
import redis
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text as sql_text

from .db import Base, engine, SessionLocal
from .sentiment_model import model
from .schemas import PredictRequest, PredictResponse, ResultResponse
from .tasks import predict_task, celery_app
from .models import Prediction
from .logger import logger

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API application")
    yield
    logger.info("API stopped gracefully")

app = FastAPI(
    title="AI Sentiment API",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api",
)

# Логирование
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s completed in %.2f ms", request.method, request.url.path, duration_ms)
    return response

# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "hint": "Only Latin letters, numbers, spaces and basic punctuation are allowed. Text must contain at least one Latin letter, 5 letters.",
        },
    )

# Health Check
# Проверка доступности БД, Redis и готовности ML-модели
@app.get("/health")
def health():
    details = {"api": "ok", "db": "unknown", "redis": "unknown", "model": "unknown"}
    overall_ok = True

    db = None
    try:
        db = SessionLocal()
        db.execute(sql_text("SELECT 1"))
        details["db"] = "ok"
    except Exception as e:
        details["db"] = f"error: {str(e)}"
        overall_ok = False
    finally:
        if db:
            db.close()

    try:
        redis_client = redis.from_url(celery_app.conf.broker_url)
        redis_client.ping()
        details["redis"] = "ok"
    except Exception as e:
        details["redis"] = f"error: {str(e)}"
        overall_ok = False

    try:
        if model is None:
            raise RuntimeError("Model instance is None")
        if not hasattr(model, "model") or model.model is None:
            raise RuntimeError("Loaded classifier is missing")
        if not hasattr(model, "vectorizer") or model.vectorizer is None:
            raise RuntimeError("Loaded vectorizer is missing")

        test_result = model.generate("This is a health check sample")
        if test_result not in {"negative", "neutral", "positive"}:
            raise RuntimeError(f"Unexpected prediction result: {test_result}")

        details["model"] = "ok"
    except Exception as e:
        details["model"] = f"error: {str(e)}"
        overall_ok = False

    if overall_ok:
        return {"status": "ok", **details}

    return JSONResponse(status_code=503, content={"status": "down", **details})

# Асинхронная очередь
# Task is sent to Celery worker
@app.post("/predict", status_code=202, response_model=PredictResponse)
def predict(req: PredictRequest):
    logger.info("Task received by API")
    task = predict_task.delay(req.text)
    return {"task_id": task.id}

# Асинхронная очередь
# Polling task result(status)
@app.get("/result/{task_id}", response_model=ResultResponse)
def result(task_id: str):
    result_obj = celery_app.AsyncResult(task_id)

    if result_obj.failed():
        return JSONResponse(status_code=500, content={"status": "failed"})

    if result_obj.ready():
        return {"status": "done", "sentiment": result_obj.result["sentiment"]}

    return {"status": "pending"}

# WebSocket status check
@app.websocket("/ws/result/{task_id}")
async def result_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            result_obj = celery_app.AsyncResult(task_id)

            if result_obj.failed():
                await websocket.send_json({"status": "failed"})
                break

            if result_obj.ready():
                await websocket.send_json(
                    {"status": "done", "sentiment": result_obj.result["sentiment"]}
                )
                break

            await websocket.send_json({"status": "pending"})
            await asyncio.sleep(1)
    finally:
        await websocket.close()

# ORM
@app.get("/history")
def history():
    db = SessionLocal()
    try:
        rows = db.query(Prediction).all()
        data = [
            {
                "id": row.id,
                "text": row.text,
                "sentiment": row.sentiment,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return data
    finally:
        db.close()