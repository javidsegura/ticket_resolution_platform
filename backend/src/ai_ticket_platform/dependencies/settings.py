 
from typing import Dict
from ai_ticket_platform.core.settings import initialize_settings
import logging


# DONT CHANGE THIS SECTION

logger = logging.getLogger(__name__)

async def get_app_settings() -> Dict:
	app_settings = initialize_settings()
	logger.debug(f"App settings: {app_settings}")
	return app_settings