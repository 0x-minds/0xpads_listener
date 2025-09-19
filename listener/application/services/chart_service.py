"""
📊 Chart Service
"""
from typing import Dict, Any
from ...application.interfaces import ICandleRepository, IMarketDataRepository, ICacheService


class ChartService:
    def __init__(self, candle_repo: ICandleRepository, market_data_repo: IMarketDataRepository, cache_service: ICacheService):
        self.candle_repo = candle_repo
        self.market_data_repo = market_data_repo
        self.cache_service = cache_service
