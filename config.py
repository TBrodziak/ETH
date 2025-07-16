import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Ethereum monitoring bot"""
    
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_TOKEN", "")
        self.telegram_user_id = os.getenv("TELEGRAM_USER_ID", "").replace("@", "")
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY", "")
        
        # Bot configuration
        self.price_change_threshold = 3.0  # Percentage change threshold
        self.check_interval = 30  # Seconds between price checks
        self.daily_report_hours = [8, 12, 16, 20]  # Hours for daily reports
        
        # API endpoints
        self.coingecko_price_url = "https://api.coingecko.com/api/v3/simple/price"
        self.coingecko_history_url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
        self.cryptopanic_url = "https://cryptopanic.com/api/v1/posts/"
        
        # Validate required environment variables
        self._validate()
    
    def _validate(self):
        """Validate that required environment variables are set"""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_TOKEN environment variable is required")
        if not self.telegram_user_id:
            raise ValueError("TELEGRAM_USER_ID environment variable is required")
        if not self.cryptopanic_api_key:
            print("Warning: CRYPTOPANIC_API_KEY not set, news features will be disabled")
    
    @property
    def has_cryptopanic_key(self) -> bool:
        """Check if CryptoPanic API key is available"""
        return bool(self.cryptopanic_api_key and self.cryptopanic_api_key != "TWÓJ_KLUCZ_API")
