import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class DataStore:
    """Simple file-based data store for bot state"""
    
    def __init__(self, filename: str = "bot_data.json"):
        self.filename = filename
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading data file: {e}")
        
        # Return default data structure
        return {
            "last_price": None,
            "last_24h_price": None,
            "last_news_timestamp": "",
            "last_daily_report": "",
            "bot_start_time": datetime.now().isoformat(),
            "total_alerts_sent": 0,
            "total_news_sent": 0,
            "last_error": ""
        }
    
    def _save_data(self):
        """Save data to file"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving data file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value by key and save"""
        self.data[key] = value
        self._save_data()
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple values at once"""
        self.data.update(updates)
        self._save_data()
    
    def increment(self, key: str, amount: int = 1):
        """Increment a numeric value"""
        current = self.data.get(key, 0)
        self.data[key] = current + amount
        self._save_data()
