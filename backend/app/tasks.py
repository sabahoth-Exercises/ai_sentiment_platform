from celery import Celery
import os
from .sentiment_model import model
from .db import SessionLocal
from .models import Prediction

# Асинхронная очередь
celery_app=Celery('tasks', broker=os.getenv('REDIS_URL'), backend=os.getenv('REDIS_URL'))
@celery_app.task
def predict_task(text:str):
    sentiment=model.generate(text[:1500])
    db=SessionLocal()
    db.add(Prediction(text=text,sentiment=sentiment))
    db.commit()
    db.close()
    return {'sentiment':sentiment}