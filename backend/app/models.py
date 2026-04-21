from sqlalchemy import Column,Integer,String,Float,DateTime
from datetime import datetime
from .db import Base
class Prediction(Base):
    __tablename__='predictions'
    id=Column(Integer, primary_key=True)
    text=Column(String(1500))
    sentiment=Column(String(50))
    created_at=Column(DateTime, default=datetime.utcnow)