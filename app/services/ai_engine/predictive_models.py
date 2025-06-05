import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import joblib
import os
from typing import Dict, Any, List, Tuple, Optional
from loguru import logger
from app.config.settings import settings

class PredictiveModels:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_storage_path = settings.MODEL_STORAGE_PATH
        os.makedirs(self.model_storage_path, exist_ok=True)

    async def train_lead_scoring_model(self, training_data: pd.DataFrame, company_id: int) -> Dict[str, Any]:
        """Entrena modelo para scoring de leads/prospectos"""
        try:
            # Preparar datos
            features, target = self._prepare_lead_data(training_data)

            if len(features) < 10:
                raise ValueError("Insuficientes datos para entrenar el modelo (mínimo 10 registros)")

            # División train/test
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, stratify=target
            )

            # Entrenar modelo
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )

            model.fit(X_train, y_train)

            # Evaluar
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)

            y_pred = model.predict(X_test)
            classification_rep = classification_report(y_test, y_pred, output_dict=True)

            # Importancia de características
            feature_importance = dict(zip(
                features.columns,
                model.feature_importances_
            ))

            # Guardar modelo
            model_key = f"lead_scoring_{company_id}"
            self.models[model_key] = model
            self._save_model(model, model_key)

            results = {
                "model_type": "lead_scoring",
                "company_id": company_id,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "train_accuracy": train_score,
                "test_accuracy": test_score,
                "classification_report": classification_rep,
                "feature_importance": feature_importance
            }

            return results

        except Exception as e:
            logger.error(f"Error training lead scoring model: {str(e)}")
            raise

    def _prepare_lead_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara los datos para el modelo de scoring"""
        # Asumiendo que 'converted' es la columna objetivo
        features = df.drop(['converted'], axis=1)
        target = df['converted']
        
        return features, target

    def _save_model(self, model: Any, model_key: str) -> None:
        """Guarda el modelo en disco"""
        model_path = os.path.join(self.model_storage_path, f"{model_key}.joblib")
        joblib.dump(model, model_path)

    def load_model(self, model_key: str) -> Optional[Any]:
        """Carga un modelo desde disco"""
        try:
            model_path = os.path.join(self.model_storage_path, f"{model_key}.joblib")
            if os.path.exists(model_path):
                return joblib.load(model_path)
            return None
        except Exception as e:
            logger.error(f"Error loading model {model_key}: {str(e)}")
            return None

    async def predict_lead_score(self, data: pd.DataFrame, company_id: int) -> np.ndarray:
        """Realiza predicciones de scoring para nuevos leads"""
        model_key = f"lead_scoring_{company_id}"
        model = self.models.get(model_key) or self.load_model(model_key)
        
        if model is None:
            raise ValueError(f"No existe modelo entrenado para company_id {company_id}")
        
        return model.predict_proba(data)[:, 1]  # Retorna probabilidades de la clase positiva
            # ... (rest of the code is cut off)