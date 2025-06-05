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
        self._load_all_models() # Cargar modelos existentes al iniciar

    async def train_lead_scoring_model(self, training_data: pd.DataFrame, company_id: int) -> Dict[str, Any]:
        """Entrena modelo para scoring de leads/prospectos"""
        try:
            # Preparar datos
            features, target = self._prepare_lead_data(training_data, company_id)

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
                "feature_importances": feature_importance,
                "status": "success",
                "message": f"Modelo de scoring de leads entrenado y guardado para la empresa {company_id}"
            }
            logger.info(results["message"])
            return results

        except ValueError as e:
            logger.error(f"Error al entrenar el modelo de scoring de leads para la empresa {company_id}: {e}")
            return {
                "model_type": "lead_scoring",
                "company_id": company_id,
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Error inesperado al entrenar el modelo de scoring de leads para la empresa {company_id}: {e}")
            return {
                "model_type": "lead_scoring",
                "company_id": company_id,
                "status": "error",
                "message": "Error interno del servidor al entrenar el modelo."
            }

    async def predict_lead_score(self, prediction_data: pd.DataFrame, company_id: int) -> List[Dict[str, Any]]:
        """Realiza predicciones de scoring de leads/prospectos"""
        model_key = f"lead_scoring_{company_id}"
        if model_key not in self.models:
            logger.warning(f"Modelo {model_key} no encontrado. Entrenando uno nuevo o cargando.")
            # Intenta cargar el modelo si no está en memoria
            try:
                self._load_model(model_key)
            except FileNotFoundError:
                logger.error(f"Modelo {model_key} no existe en disco. No se puede predecir.")
                return [{"status": "error", "message": f"Modelo para la empresa {company_id} no entrenado."}]
            except Exception as e:
                logger.error(f"Error al cargar el modelo {model_key}: {e}")
                return [{"status": "error", "message": f"Error al cargar el modelo para la empresa {company_id}."}]

        try:
            model = self.models[model_key]
            # Asegurarse de que el encoder exista para esta compañía antes de preparar los datos de predicción
            if company_id not in self.encoders:
                # Esto es un caso borde, ya que el encoder debería guardarse y cargarse con el modelo.
                # Si llega a este punto, significa que el encoder no se cargó correctamente.
                # Se podría re-entrenar un encoder dummy o pedir al usuario que re-entrene el modelo.
                logger.warning(f"Encoder para la empresa {company_id} no encontrado. La predicción podría fallar si hay datos categóricos nuevos.")
                # Para un sistema robusto, aquí se debería manejar la regeneración del encoder o un error claro.
                # Por simplicidad, se asumirá que los datos ya están en el formato correcto o que el encoder se manejará en _prepare_lead_data si es necesario.

            processed_data = self._prepare_lead_data_for_prediction(prediction_data, company_id)

            if processed_data.empty:
                return [{"status": "error", "message": "Datos de entrada vacíos o no válidos para la predicción."}]

            predictions = model.predict(processed_data)
            probabilities = model.predict_proba(processed_data)
            # Suponiendo que la clase positiva es 1
            positive_probabilities = probabilities[:, model.classes_.tolist().index(1)] if 1 in model.classes_ else None

            results = []
            for i, _id in enumerate(prediction_data.get('id', range(len(predictions)))):
                result_item = {
                    "id": str(_id), # Asegurar que el ID sea string para consistencia JSON
                    "predicted_score": int(predictions[i]),
                    "status": "success",
                    "message": "Predicción exitosa"
                }
                if positive_probabilities is not None:
                    result_item["probability_of_positive_class"] = float(positive_probabilities[i])
                results.append(result_item)
            return results

        except ValueError as e:
            logger.error(f"Error en los datos de entrada para la predicción del modelo de scoring de leads para la empresa {company_id}: {e}")
            return [{"status": "error", "message": f"Error en los datos de entrada: {e}"}]
        except Exception as e:
            logger.error(f"Error inesperado al predecir el score de leads para la empresa {company_id}: {e}")
            return [{"status": "error", "message": "Error interno del servidor al realizar la predicción."}]

    def _prepare_lead_data(self, data: pd.DataFrame, company_id: int) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara los datos para el entrenamiento del modelo de scoring de leads."""
        df = data.copy()

        # Manejo de valores nulos: Imputar con la moda para categóricos, media/mediana para numéricos.
        for column in df.columns:
            if df[column].dtype == 'object':
                mode_val = df[column].mode()[0]
                df[column] = df[column].fillna(mode_val)
            else:
                mean_val = df[column].mean()
                df[column] = df[column].fillna(mean_val)

        # Codificación de variables categóricas (Label Encoding)
        # Se guarda el encoder para usarlo en la predicción
        for column in df.select_dtypes(include=['object']).columns:
            if column != 'target_variable': # Asumiendo que 'target_variable' es la columna objetivo
                le = LabelEncoder()
                df[column] = le.fit_transform(df[column])
                if company_id not in self.encoders:
                    self.encoders[company_id] = {}
                self.encoders[company_id][column] = le
        
        # Asumiendo que la columna objetivo se llama 'target_variable' o similar en tu dataset
        # Asegúrate de que esta columna exista y sea numérica (0 o 1)
        if 'is_converted' not in df.columns: # Reemplaza 'is_converted' con el nombre real de tu columna objetivo
            raise ValueError("La columna 'is_converted' (variable objetivo) no se encuentra en los datos de entrenamiento.")
        
        target = df['is_converted'] # Reemplaza 'is_converted' con el nombre real de tu columna objetivo
        features = df.drop(columns=['is_converted']) # Reemplaza 'is_converted' con el nombre real de tu columna objetivo
        
        # Escalado de características numéricas (StandardScaler)
        numeric_features = features.select_dtypes(include=np.number).columns
        if not numeric_features.empty:
            scaler = StandardScaler()
            features[numeric_features] = scaler.fit_transform(features[numeric_features])
            self.scalers[company_id] = scaler # Guardar el scaler para usarlo en la predicción

        return features, target

    def _prepare_lead_data_for_prediction(self, data: pd.DataFrame, company_id: int) -> pd.DataFrame:
        """Prepara los datos de entrada para la predicción."""
        df = data.copy()

        # Manejo de valores nulos (usando la moda/media de los datos de entrenamiento si es posible)
        # Si no hay datos de entrenamiento o no se guardó el contexto, se imputa con la moda/media de los datos actuales
        for column in df.columns:
            if df[column].dtype == 'object':
                # Idealmente, usar la moda del conjunto de entrenamiento. Si no está disponible, usar la moda de los datos de predicción.
                mode_val = df[column].mode()[0] if not df[column].mode().empty else None
                df[column] = df[column].fillna(mode_val)
            else:
                # Idealmente, usar la media del conjunto de entrenamiento. Si no está disponible, usar la media de los datos de predicción.
                mean_val = df[column].mean()
                df[column] = df[column].fillna(mean_val)

        # Aplicar Label Encoding con los encoders guardados
        if company_id in self.encoders:
            for column, le in self.encoders[company_id].items():
                if column in df.columns:
                    # Manejar categorías nuevas: transformar con .transform y, si hay errores (categorías no vistas),
                    # asignarlas a una categoría predefinida (ej. -1 o la categoría más común)
                    try:
                        df[column] = le.transform(df[column])
                    except ValueError:
                        # Si hay categorías no vistas, las reemplazamos por un valor NaN o un valor por defecto.
                        # Luego, podemos imputar estos NaNs.
                        df[column] = df[column].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
                        logger.warning(f"Nuevas categorías detectadas en la columna '{column}' para la empresa {company_id}. Se han asignado a -1.")
        else:
            logger.warning(f"No se encontraron encoders para la empresa {company_id}. Las columnas categóricas no serán codificadas.")
            # Si no hay encoders, se podría intentar One-Hot Encoding si es una expectativa del modelo,
            # o simplemente dejarlo como está si el modelo puede manejar objetos (poco probable con RandomForest directo).
            # Para la predicción, es crucial que las columnas de entrada coincidan con las de entrenamiento.
            # Aquí, si no hay encoder, se convertirán las columnas categóricas a numéricas si es posible,
            # o se lanzará un error si el modelo no puede manejarlas.
            for column in df.select_dtypes(include=['object']).columns:
                 # Si no hay encoder guardado, y hay columnas de objeto, el modelo fallará.
                 # Podríamos optar por dummy variables si el modelo lo espera, o simplemente reportar un error.
                 # Por simplicidad aquí, si no hay encoder, se asume que los datos ya están numéricos o el modelo puede procesarlos.
                pass # No hacer nada si no hay encoder para aplicar.

        # Aplicar Standard Scaling con el scaler guardado
        numeric_features = df.select_dtypes(include=np.number).columns
        if company_id in self.scalers and not numeric_features.empty:
            scaler = self.scalers[company_id]
            df[numeric_features] = scaler.transform(df[numeric_features])
        elif not numeric_features.empty:
            logger.warning(f"No se encontró scaler para la empresa {company_id}. Las columnas numéricas no serán escaladas.")
            # Si no hay scaler, y se espera que las características estén escaladas, esto podría impactar la predicción.

        return df

    def _save_model(self, model: Any, model_key: str):
        """Guarda un modelo y sus preprocesadores asociados."""
        model_path = os.path.join(self.model_storage_path, f"{model_key}.joblib")
        joblib.dump(model, model_path)
        logger.info(f"Modelo {model_key} guardado en {model_path}")

        # Guardar scalers y encoders asociados
        if model_key.startswith("lead_scoring_"):
            company_id = int(model_key.split('_')[-1])
            if company_id in self.scalers:
                scaler_path = os.path.join(self.model_storage_path, f"scaler_{company_id}.joblib")
                joblib.dump(self.scalers[company_id], scaler_path)
                logger.info(f"Scaler para la empresa {company_id} guardado en {scaler_path}")
            if company_id in self.encoders:
                encoder_path = os.path.join(self.model_storage_path, f"encoder_{company_id}.joblib")
                joblib.dump(self.encoders[company_id], encoder_path)
                logger.info(f"Encoder para la empresa {company_id} guardado en {encoder_path}")

    def _load_model(self, model_key: str):
        """Carga un modelo específico y sus preprocesadores asociados."""
        model_path = os.path.join(self.model_storage_path, f"{model_key}.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"El archivo del modelo {model_path} no existe.")
        self.models[model_key] = joblib.load(model_path)
        logger.info(f"Modelo {model_key} cargado desde {model_path}")

        # Cargar scalers y encoders asociados
        if model_key.startswith("lead_scoring_"):
            company_id = int(model_key.split('_')[-1])
            scaler_path = os.path.join(self.model_storage_path, f"scaler_{company_id}.joblib")
            if os.path.exists(scaler_path):
                self.scalers[company_id] = joblib.load(scaler_path)
                logger.info(f"Scaler para la empresa {company_id} cargado desde {scaler_path}")
            else:
                logger.warning(f"Scaler para la empresa {company_id} no encontrado en {scaler_path}.")

            encoder_path = os.path.join(self.model_storage_path, f"encoder_{company_id}.joblib")
            if os.path.exists(encoder_path):
                self.encoders[company_id] = joblib.load(encoder_path)
                logger.info(f"Encoder para la empresa {company_id} cargado desde {encoder_path}")
            else:
                logger.warning(f"Encoder para la empresa {company_id} no encontrado en {encoder_path}.")

    def _load_all_models(self):
        """Carga todos los modelos y sus preprocesadores del directorio de almacenamiento."""
        for filename in os.listdir(self.model_storage_path):
            if filename.endswith(".joblib") and not (filename.startswith("scaler_") or filename.startswith("encoder_")):
                model_key = filename.replace(".joblib", "")
                try:
                    self._load_model(model_key)
                except Exception as e:
                    logger.error(f"Error al cargar el modelo {model_key}: {e}")

    # Puedes añadir un método similar para el modelo de predicción de ventas
    # async def train_sales_prediction_model(self, training_data: pd.DataFrame, company_id: int) -> Dict[str, Any]:
    #     """Entrena modelo para predicción de ventas/ingresos"""
    #     pass # Implementación similar pero con RandomForestRegressor

    # async def predict_sales(self, prediction_data: pd.DataFrame, company_id: int) -> List[Dict[str, Any]]:
    #     """Realiza predicciones de ventas/ingresos"""
    #     pass # Implementación similar