import joblib
import pandas as pd
import os
from datetime import datetime
from backend.utils.logger import logger

class PricePredictor:
    def __init__(self, model_dir="crautos_analisis_datos/models"):
        self.model_path = os.path.join(model_dir, "car_price_model.pkl")
        self.columns_path = os.path.join(model_dir, "model_columns.pkl")
        self.model = None
        self.model_columns = None
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.columns_path):
                self.model = joblib.load(self.model_path)
                self.model_columns = joblib.load(self.columns_path)
                logger.info("Machine learning model and columns loaded successfully.")
            else:
                logger.warning(f"Model files not found in {self.model_path} or {self.columns_path}. Price prediction will not work.")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")

    def predict_price(self, marca: str, modelo: str, año: int, kilometraje: float,
                      cilindrada: float, combustible: str, transmision: str, cantidad_extras: int) -> float:
        if not self.model or getattr(self, 'model_columns', None) is None:
            raise ValueError("Model is not loaded.")

        antiguedad = max(0, datetime.now().year - año)

        input_data = {
            "antiguedad": [antiguedad],
            "kilometraje": [kilometraje],
            "cilindrada": [cilindrada],
            "marca": [marca],
            "modelo": [modelo],
            "transmision": [transmision],
            "cantidad_extras": [cantidad_extras],
            "combustible": [combustible],
        }

        input_df = pd.DataFrame(input_data)

        # One-hot encode using pandas get_dummies
        input_df_encoded = pd.get_dummies(input_df)

        # Align with model columns to ensure exact match of features
        input_df_aligned = input_df_encoded.reindex(columns=self.model_columns, fill_value=0)

        try:
            prediction = self.model.predict(input_df_aligned)[0]
            return float(prediction)
        except Exception as e:
            logger.error(f"Error predicting price: {e}")
            raise ValueError(f"Failed to predict price: {e}")

# Create a singleton instance
price_predictor = PricePredictor()
