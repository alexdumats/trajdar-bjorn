# Data Service - Legacy stub
# This service has been refactored into separate market_analyst and news_analyst services
# Kept for backward compatibility with deployment scripts

import logging
logger = logging.getLogger(__name__)

class DataService:
    """Legacy data service - functionality moved to market_analyst and news_analyst"""
    
    def __init__(self):
        logger.warning("DataService is deprecated - use market_analyst and news_analyst services")
        
    def get_health(self):
        return {"status": "deprecated", "message": "Use market_analyst and news_analyst services"}

if __name__ == "__main__":
    logger.info("DataService stub - functionality moved to specialized analyst services")