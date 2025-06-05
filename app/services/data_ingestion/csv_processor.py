import pandas as pd
import numpy as np
from typing import Dict, Any, List
from loguru import logger
from app.utils.exceptions import DataProcessingError

class CSVProcessor:
    def __init__(self):
        self.supported_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    async def process_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Procesa archivo CSV y retorna datos normalizados"""
        try:
            # Intentar diferentes encodings
            df = None
            for encoding in self.supported_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise DataProcessingError("No se pudo leer el archivo CSV con ningún encoding soportado")

            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            # Detectar tipo de datos (ventas, clientes, etc.)
            data_type = self._detect_data_type(df.columns.tolist())

            # Validar datos
            validation_results = self._validate_data(df, data_type)

            # Limpiar y normalizar datos
            cleaned_df = self._clean_data(df, data_type)

            return {
                "data_type": data_type,
                "records": cleaned_df.to_dict('records'),
                "record_count": len(cleaned_df),
                "columns": cleaned_df.columns.tolist(),
                "validation_results": validation_results,
                "summary_stats": self._generate_summary_stats(cleaned_df, data_type)
            }

        except Exception as e:
            logger.error(f"Error procesando CSV: {str(e)}")
            raise DataProcessingError(f"Error procesando archivo CSV: {str(e)}")

    def _detect_data_type(self, columns: List[str]) -> str:
        """Detecta el tipo de datos basado en las columnas"""
        sales_keywords = ['venta', 'precio', 'total', 'cantidad', 'revenue', 'sale']
        customer_keywords = ['cliente', 'customer', 'email', 'telefono', 'phone']
        campaign_keywords = ['campaign', 'campaña', 'ad', 'impression', 'click']

        sales_score = sum(1 for col in columns if any(keyword in col for keyword in sales_keywords))
        customer_score = sum(1 for col in columns if any(keyword in col for keyword in customer_keywords))
        campaign_score = sum(1 for col in columns if any(keyword in col for keyword in campaign_keywords))

        if sales_score > customer_score and sales_score > campaign_score:
            return "sales"
        elif customer_score > campaign_score:
            return "customers"
        elif campaign_score > 0:
            return "campaigns"
        else:
            return "unknown"

    def _validate_data(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """Valida la calidad de los datos"""
        total_rows = len(df)

        validation = {
            "total_rows": total_rows,
            "empty_rows": df.isnull().all(axis=1).sum(),
            "duplicate_rows": df.duplicated().sum(),
            "missing_data_percentage": (df.isnull().sum() / total_rows * 100).to_dict(),
            "data_types": df.dtypes.astype(str).to_dict()
        }

        # Validaciones específicas por tipo
        if data_type == "sales":
            validation["sales_specific"] = self._validate_sales_data(df)
        elif data_type == "customers":
            validation["customer_specific"] = self._validate_customer_data(df)

        return validation

    def _clean_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Limpia y normaliza los datos"""
        # Remover filas completamente vacías
        df = df.dropna(how='all')

        # Normalizar strings
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()

        # Convertir fechas
        date_columns = [col for col in df.columns if 'fecha' in col or 'date' in col]
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
            except:
                pass

        # Convertir números
        numeric_keywords = ['precio', 'total', 'cantidad', 'value', 'amount']
        for col in df.columns:
            if any(keyword in col for keyword in numeric_keywords):
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _generate_summary_stats(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """Genera estadísticas resumen"""
        stats = {
            "record_count": len(df),
            "column_count": len(df.columns),
            "data_type": data_type
        }

        # Estadísticas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()

        return stats