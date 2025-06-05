from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from app.config.settings import settings
from app.utils.exceptions import APIConnectionError

class GoogleAdsConnector:
    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa el cliente de Google Ads"""
        try:
            if not all([
                settings.GOOGLE_ADS_DEVELOPER_TOKEN,
                settings.GOOGLE_ADS_CLIENT_ID,
                settings.GOOGLE_ADS_CLIENT_SECRET
            ]):
                logger.warning("Credenciales de Google Ads no configuradas completamente")
                return

            self.client = GoogleAdsClient.load_from_dict({
                "developer_token": settings.GOOGLE_ADS_DEVELOPER_TOKEN,
                "client_id": settings.GOOGLE_ADS_CLIENT_ID,
                "client_secret": settings.GOOGLE_ADS_CLIENT_SECRET,
                "use_proto_plus": True
            })

        except Exception as e:
            logger.error(f"Error inicializando cliente Google Ads: {str(e)}")

    async def get_campaign_data(self, customer_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Obtiene datos de campañas de Google Ads"""
        if not self.client:
            raise APIConnectionError("Cliente de Google Ads no inicializado")

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            # Fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversion_value_micros,
                segments.date
            FROM campaign
            WHERE segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}'
                 AND '{end_date.strftime('%Y-%m-%d')}'
            ORDER BY segments.date DESC
            """

            response = ga_service.search_stream(customer_id=customer_id, query=query)

            campaigns_data = []
            for batch in response:
                for row in batch.results:
                    campaigns_data.append({
                        "campaign_id": row.campaign.id,
                        "campaign_name": row.campaign.name,
                        "campaign_status": row.campaign.status.name,
                        "date": row.segments.date,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": row.metrics.cost_micros / 1_000_000,  # Convertir de micros
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversion_value_micros / 1_000_000
                    })

            return {
                "data_type": "google_ads_campaigns",
                "records": campaigns_data,
                "record_count": len(campaigns_data),
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "customer_id": customer_id
            }

        except GoogleAdsException as ex:
            logger.error(f"Error en Google Ads API: {ex}")
            raise APIConnectionError(f"Error conectando con Google Ads: {str(ex)}")
        except Exception as e:
            logger.error(f"Error obteniendo datos de Google Ads: {str(e)}")
            raise APIConnectionError(f"Error obteniendo datos: {str(e)}")

    async def get_customer_accounts(self, manager_customer_id: str) -> List[Dict[str, Any]]:
        """Obtiene las cuentas de cliente disponibles"""
        if not self.client:
            raise APIConnectionError("Cliente de Google Ads no inicializado")

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            query = """
            SELECT
                customer_client.client_customer,
                customer_client.level,
                customer_client.manager,
                customer_client.descriptive_name,
                customer_client.currency_code,
                customer_client.time_zone,
                customer_client.id
            FROM customer_client
            WHERE customer_client.level <= 1
            """

            response = ga_service.search(customer_id=manager_customer_id, query=query)

            accounts = []
            for row in response:
                accounts.append({
                    "customer_id": row.customer_client.id,
                    "name": row.customer_client.descriptive_name,
                    "currency": row.customer_client.currency_code,
                    "timezone": row.customer_client.time_zone,
                    "is_manager": row.customer_client.manager
                })

            return accounts

        except Exception as e:
            logger.error(f"Error obteniendo cuentas de cliente: {str(e)}")
            raise APIConnectionError(f"Error obteniendo cuentas: {str(e)}")