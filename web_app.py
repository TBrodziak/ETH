from flask import Flask, render_template, jsonify, request
import threading
import time
from datetime import datetime
from bot import EthereumBot
from scheduler import TaskScheduler
from data_store import DataStore
from config import Config

app = Flask(__name__)
bot = None
scheduler = None
data_store = DataStore()
config = Config()

def create_bot_instance():
    """Create and return bot instance"""
    global bot
    if bot is None:
        bot = EthereumBot()
    return bot

def start_bot_monitoring():
    """Start bot monitoring in background"""
    global scheduler
    
    if scheduler and scheduler.running:
        return
    
    bot_instance = create_bot_instance()
    scheduler = TaskScheduler()
    
    # Add scheduled tasks
    scheduler.add_periodic_task(
        bot_instance.check_price_alerts,
        config.check_interval,
        "Price Monitoring"
    )
    
    scheduler.add_hourly_task(
        bot_instance.send_daily_report,
        config.daily_report_hours,
        0,
        "Daily Reports"
    )
    
    scheduler.add_periodic_task(
        bot_instance.check_news_updates,
        300,  # Check news every 5 minutes
        "News Updates"
    )
    
    scheduler.start()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('simple.html')

@app.route('/advanced')
def advanced():
    """Advanced dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get bot status"""
    bot_instance = create_bot_instance()
    current_price = bot_instance.get_eth_price()
    
    status = {
        "bot_running": scheduler.running if scheduler else False,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_price": current_price,
        "last_price": data_store.get("last_price"),
        "bot_start_time": data_store.get("bot_start_time"),
        "total_alerts_sent": data_store.get("total_alerts_sent", 0),
        "total_news_sent": data_store.get("total_news_sent", 0),
        "last_error": data_store.get("last_error", ""),
        "config": {
            "price_threshold": config.price_change_threshold,
            "check_interval": config.check_interval,
            "daily_report_hours": config.daily_report_hours,
            "news_enabled": config.has_cryptopanic_key
        }
    }
    
    if scheduler:
        status["scheduler"] = scheduler.get_status()
    
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start bot monitoring"""
    try:
        start_bot_monitoring()
        return jsonify({"success": True, "message": "Bot started successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop bot monitoring"""
    global scheduler
    try:
        if scheduler:
            scheduler.stop()
            scheduler = None
        return jsonify({"success": True, "message": "Bot stopped successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/test-telegram', methods=['POST'])
def api_test_telegram():
    """Test Telegram connection"""
    try:
        bot_instance = create_bot_instance()
        success = bot_instance.send_telegram_message(
            "🧪 <b>Test Message</b>\n\nTelegram connection is working!"
        )
        if success:
            return jsonify({"success": True, "message": "Test message sent successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to send test message"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/manual-check', methods=['POST'])
def api_manual_check():
    """Manually trigger a check cycle"""
    try:
        bot_instance = create_bot_instance()
        bot_instance.run_check_cycle()
        return jsonify({"success": True, "message": "Manual check completed"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/price-history')
def api_price_history():
    """Get price history data"""
    try:
        bot_instance = create_bot_instance()
        price_data = bot_instance.get_eth_24h_data()
        
        if price_data:
            current, price_24h_ago = price_data
            change = current - price_24h_ago
            change_percent = (change / price_24h_ago) * 100
            
            return jsonify({
                "current_price": current,
                "price_24h_ago": price_24h_ago,
                "change": change,
                "change_percent": change_percent
            })
        else:
            return jsonify({"error": "Unable to fetch price history"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/get-chat-updates')
def api_get_chat_updates():
    """Get recent chat updates to help find user chat ID"""
    try:
        bot_instance = create_bot_instance()
        response = requests.get(f"{bot_instance.telegram_api_url}/getUpdates", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("result"):
                updates = []
                for update in data["result"][-5:]:  # Last 5 updates
                    if "message" in update:
                        msg = update["message"]
                        chat = msg["chat"]
                        updates.append({
                            "chat_id": chat["id"],
                            "username": chat.get("username", ""),
                            "first_name": chat.get("first_name", ""),
                            "text": msg.get("text", ""),
                            "date": msg["date"]
                        })
                return jsonify({"success": True, "updates": updates})
            else:
                return jsonify({"success": False, "message": "No updates found"})
        else:
            return jsonify({"success": False, "message": f"HTTP error: {response.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    # Auto-start the bot
    try:
        start_bot_monitoring()
        print("🌐 Web dashboard starting on http://0.0.0.0:5000")
    except Exception as e:
        print(f"Warning: Could not auto-start bot: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
