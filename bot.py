import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import Config
from data_store import DataStore

class EthereumBot:
    """Ethereum monitoring bot with Telegram notifications"""
    
    def __init__(self):
        self.config = Config()
        self.store = DataStore()
        
        # Initialize Telegram bot using HTTP API
        self.telegram_api_url = f"https://api.telegram.org/bot{self.config.telegram_token}"
        
        try:
            # Test the connection
            response = requests.get(f"{self.telegram_api_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    print(f"✅ Telegram bot initialized successfully: @{bot_info['result']['username']}")
                else:
                    raise Exception(f"Telegram API error: {bot_info.get('description', 'Unknown error')}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to initialize Telegram bot: {e}")
            raise
    
    def get_crypto_price(self, crypto_id: str) -> Optional[float]:
        """Get current cryptocurrency price from CoinGecko"""
        try:
            cache_key = f"cached_{crypto_id}_price"
            params = {
                "ids": crypto_id,
                "vs_currencies": "usd"
            }
            response = requests.get(self.config.coingecko_price_url, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"Rate limited by CoinGecko, using cached {crypto_id} price")
                cached_price = self.store.get(cache_key)
                if cached_price:
                    return cached_price
                return None
            
            response.raise_for_status()
            data = response.json()
            price = float(data[crypto_id]["usd"])
            # Cache the successful price fetch
            self.store.set(cache_key, price)
            return price
        except Exception as e:
            print(f"Error fetching {crypto_id} price: {e}")
            self.store.set("last_error", f"Price fetch error: {e}")
            # Return cached price if available
            cached_price = self.store.get(f"cached_{crypto_id}_price")
            return cached_price

    def get_eth_price(self) -> Optional[float]:
        """Get current Ethereum price from CoinGecko"""
        return self.get_crypto_price("ethereum")

    def get_link_price(self) -> Optional[float]:
        """Get current Chainlink price from CoinGecko"""
        return self.get_crypto_price("chainlink")
    
    def get_eth_24h_data(self) -> Optional[Tuple[float, float]]:
        """Get Ethereum price data for 24h change calculation"""
        try:
            params = {
                "vs_currency": "usd",
                "days": "1"
            }
            response = requests.get(self.config.coingecko_history_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = data["prices"]
            if len(prices) >= 2:
                current_price = prices[-1][1]  # Latest price
                price_24h_ago = prices[0][1]   # Price 24h ago
                return current_price, price_24h_ago
            return None
        except Exception as e:
            print(f"Error fetching 24h data: {e}")
            return None
    
    def get_crypto_news(self) -> List[Dict]:
        """Get latest crypto news from CryptoPanic"""
        if not self.config.has_cryptopanic_key:
            return []
        
        try:
            params = {
                "auth_token": self.config.cryptopanic_api_key,
                "currencies": "ETH",
                "filter": "important",
                "public": "true"
            }
            response = requests.get(self.config.cryptopanic_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and data["results"]:
                return data["results"]
            return []
        except Exception as e:
            print(f"Error fetching news: {e}")
            self.store.set("last_error", f"News fetch error: {e}")
            return []
    
    def send_telegram_message(self, message: str) -> bool:
        """Send message via Telegram"""
        try:
            # Handle both username (@username) and user ID formats
            chat_id = self.config.telegram_user_id
            if not chat_id.startswith("@") and not chat_id.isdigit():
                chat_id = f"@{chat_id}"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            response = requests.post(
                f"{self.telegram_api_url}/sendMessage",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
                else:
                    error_msg = result.get("description", "Unknown error")
                    print(f"Telegram API error: {error_msg}")
                    
                    # If chat not found, provide helpful instructions
                    if "chat not found" in error_msg.lower():
                        print(f"\n❌ Chat ID '{chat_id}' not found!")
                        print("📱 To fix this:")
                        print("1. Start a chat with your bot by sending /start to @my_very_cool_eth_bot")
                        print("2. Or get your numeric chat ID by sending any message to the bot")
                        print("3. Then update TELEGRAM_USER_ID in .env with your numeric ID")
                    
                    self.store.set("last_error", f"Telegram API error: {error_msg}")
                    return False
            else:
                print(f"Telegram HTTP error: {response.status_code}")
                self.store.set("last_error", f"Telegram HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Telegram error: {e}")
            self.store.set("last_error", f"Telegram error: {e}")
            return False
    
    def check_price_alerts(self):
        """Check for significant price changes and send alerts"""
        # Check ETH price alerts
        self._check_crypto_alert("ethereum", "ETH")
        # Check LINK price alerts
        self._check_crypto_alert("chainlink", "LINK")

    def _check_crypto_alert(self, crypto_id: str, symbol: str):
        """Check price alerts for a specific cryptocurrency"""
        current_price = self.get_crypto_price(crypto_id)
        if current_price is None:
            return
        
        last_price_key = f"last_{crypto_id}_price"
        last_price = self.store.get(last_price_key)
        
        if last_price is not None:
            price_change = current_price - last_price
            price_change_percent = (price_change / last_price) * 100
            
            if abs(price_change_percent) >= self.config.price_change_threshold:
                direction = "📈" if price_change > 0 else "📉"
                message = (
                    f"{direction} <b>{symbol} Price Alert</b>\n\n"
                    f"💰 Current Price: <b>${current_price:,.2f}</b>\n"
                    f"📊 Change: <b>{price_change_percent:+.2f}%</b> "
                    f"(${price_change:+.2f})\n"
                    f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                if self.send_telegram_message(message):
                    self.store.increment("total_alerts_sent")
                    print(f"🚨 {symbol} alert sent: {price_change_percent:+.2f}%")
        
        # Update stored price
        self.store.set(last_price_key, current_price)
        print(f"💰 Current {symbol} price: ${current_price:,.2f}")
    
    def send_daily_report(self):
        """Send daily price report"""
        current_hour = datetime.now().hour
        last_report_date = self.store.get("last_daily_report", "")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we should send a daily report
        if (current_hour in self.config.daily_report_hours and 
            last_report_date != f"{today_str}-{current_hour}"):
            
            current_price = self.get_eth_price()
            if current_price is None:
                return
            
            # Get 24h change data
            price_data = self.get_eth_24h_data()
            change_text = ""
            if price_data:
                current, price_24h_ago = price_data
                change_24h = current - price_24h_ago
                change_24h_percent = (change_24h / price_24h_ago) * 100
                direction = "📈" if change_24h > 0 else "📉"
                change_text = f"\n📊 24h Change: <b>{change_24h_percent:+.2f}%</b> (${change_24h:+.2f}) {direction}"
            
            time_emoji = {8: "🌅", 12: "☀️", 16: "🌇", 20: "🌙"}.get(current_hour, "⏰")
            
            message = (
                f"{time_emoji} <b>ETH Daily Report</b>\n\n"
                f"💰 Current Price: <b>${current_price:,.2f}</b>"
                f"{change_text}\n"
                f"⏰ Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if self.send_telegram_message(message):
                self.store.set("last_daily_report", f"{today_str}-{current_hour}")
                print(f"📊 Daily report sent for {current_hour}:00")

    def send_daily_comparison(self):
        """Send daily price comparison at 8 AM"""
        current_hour = datetime.now().hour
        last_comparison_date = self.store.get("last_daily_comparison", "")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Only send at 8 AM and once per day
        if (current_hour == self.config.daily_comparison_hour and 
            last_comparison_date != today_str):
            
            message_parts = ["🌅 <b>Daily Price Comparison</b>\n"]
            
            # Get prices for both cryptocurrencies
            for crypto_id, symbol in [("ethereum", "ETH"), ("chainlink", "LINK")]:
                current_price = self.get_crypto_price(crypto_id)
                yesterday_price = self.store.get(f"yesterday_{crypto_id}_price")
                
                if current_price and yesterday_price:
                    change = current_price - yesterday_price
                    change_percent = (change / yesterday_price) * 100
                    direction = "📈" if change > 0 else "📉"
                    
                    message_parts.append(
                        f"\n💰 <b>{symbol}</b>\n"
                        f"Today: ${current_price:,.2f}\n"
                        f"Yesterday: ${yesterday_price:,.2f}\n"
                        f"Change: <b>{change_percent:+.2f}%</b> (${change:+.2f}) {direction}"
                    )
                elif current_price:
                    message_parts.append(
                        f"\n💰 <b>{symbol}</b>\n"
                        f"Current: ${current_price:,.2f}\n"
                        f"Yesterday: No data available"
                    )
            
            message_parts.append(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            message = "\n".join(message_parts)
            
            if self.send_telegram_message(message):
                self.store.set("last_daily_comparison", today_str)
                print("📊 Daily comparison sent at 8:00 AM")
                
            # Store today's prices as yesterday's for tomorrow's comparison
            for crypto_id in ["ethereum", "chainlink"]:
                current_price = self.get_crypto_price(crypto_id)
                if current_price:
                    self.store.set(f"yesterday_{crypto_id}_price", current_price)
    
    def check_news_updates(self):
        """Check for new crypto news and send updates"""
        if not self.config.has_cryptopanic_key:
            return
        
        news_items = self.get_crypto_news()
        last_news_timestamp = self.store.get("last_news_timestamp", "")
        
        new_items = []
        latest_timestamp = last_news_timestamp
        
        for item in news_items:
            if item["published_at"] > last_news_timestamp:
                new_items.append(item)
                if item["published_at"] > latest_timestamp:
                    latest_timestamp = item["published_at"]
        
        # Send new news items (limit to 3 most recent)
        for item in new_items[:3]:
            title = item.get("title", "No title")
            url = item.get("url", "")
            source = item.get("source", {}).get("title", "Unknown")
            
            message = (
                f"📰 <b>Crypto News</b>\n\n"
                f"📄 <b>{title}</b>\n"
                f"🏢 Source: {source}\n"
                f"🔗 {url}"
            )
            
            if self.send_telegram_message(message):
                self.store.increment("total_news_sent")
                print(f"📰 News sent: {title[:50]}...")
                time.sleep(2)  # Avoid rate limiting
        
        if latest_timestamp > last_news_timestamp:
            self.store.set("last_news_timestamp", latest_timestamp)
    
    def run_check_cycle(self):
        """Run a complete check cycle"""
        print(f"\n🔄 Running check cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Check for price alerts
            self.check_price_alerts()
            
            # Send daily reports if needed
            self.send_daily_report()
            
            # Check for news updates
            self.check_news_updates()
            
            # Clear any previous errors
            if self.store.get("last_error"):
                self.store.set("last_error", "")
                
        except Exception as e:
            error_msg = f"Unexpected error in check cycle: {e}"
            print(f"❌ {error_msg}")
            self.store.set("last_error", error_msg)
    
    def start_monitoring(self):
        """Start the continuous monitoring loop"""
        # Send startup message
        startup_msg = (
            f"✅ <b>ETH Monitoring Bot Started</b>\n\n"
            f"🎯 Price Alert Threshold: {self.config.price_change_threshold}%\n"
            f"📊 Daily Reports: {', '.join(map(str, self.config.daily_report_hours))}:00\n"
            f"📰 News Updates: {'Enabled' if self.config.has_cryptopanic_key else 'Disabled'}\n"
            f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        self.send_telegram_message(startup_msg)
        self.store.set("bot_start_time", datetime.now().isoformat())
        
        print("🚀 ETH Monitoring Bot started successfully!")
        print(f"💡 Checking every {self.config.check_interval} seconds")
        print(f"📊 Daily reports at: {self.config.daily_report_hours}")
        
        while True:
            try:
                self.run_check_cycle()
                time.sleep(self.config.check_interval)
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.send_telegram_message("🛑 <b>ETH Monitoring Bot Stopped</b>")
                break
            except Exception as e:
                print(f"❌ Critical error: {e}")
                time.sleep(60)  # Wait longer on critical errors
