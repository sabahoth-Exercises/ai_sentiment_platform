from pydantic import BaseModel, Field


# Валидация данных
class PredictRequest(BaseModel):
    text:str = Field(..., min_length=3, max_length=1500, example='I love this app')
class PredictResponse(BaseModel):
    task_id:str
class ResultResponse(BaseModel):
    status:str
    sentiment:str|None=None