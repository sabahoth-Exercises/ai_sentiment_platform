# Изоляция ML-логики
# Управление ресурсами

import os
import joblib
import logging

# Логирование
logger = logging.getLogger(__name__)

class SentimentModel:
    def __init__(self):
        base_dir = os.path.dirname(__file__)

        model_path = os.path.join(base_dir, "utilities", "best_model.pkl")
        vectorizer_path = os.path.join(base_dir, "utilities", "vectorizer.pkl")

        logger.info("Loading ML model...")

        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

        logger.info("Model loaded successfully")

    def generate(self, text: str):
        # Ограничение ресурсов
        text = text[:1500]
        X = self.vectorizer.transform([text])
        pred = self.model.predict(X)[0]

    
        # 3-class mapping
        label_map = {
            0: "negative",
            1: "neutral",
            2: "positive"
        }

        return label_map.get(pred, "unknown")

# Singleton instance (loaded once)
model = SentimentModel()