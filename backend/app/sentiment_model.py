# Изоляция ML-логики
# Управление ресурсами

import os
import joblib
import logging

logger = logging.getLogger(__name__)

class SentimentModel:
    def __init__(self):
        model_dir = os.getenv("MODEL_DIR", "/models")
        model_filename = os.getenv("MODEL_FILENAME", "best_model.pkl")
        vectorizer_filename = os.getenv("VECTORIZER_FILENAME", "vectorizer.pkl")

        model_path = os.path.join(model_dir, model_filename)
        vectorizer_path = os.path.join(model_dir, vectorizer_filename)

        logger.info("Loading ML model...")

        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

        logger.info("Model loaded successfully")

    def generate(self, text: str):
        text = text[:1500]
        X = self.vectorizer.transform([text])
        pred = self.model.predict(X)[0]

        label_map = {
            0: "negative",
            1: "neutral",
            2: "positive"
        }

        sentiment = label_map.get(pred, "unknown")
        return sentiment


model = SentimentModel()