#!/usr/bin/env python3
"""
Ethereum Monitoring Bot - Main Entry Point

This bot monitors Ethereum prices and sends Telegram notifications for:
- Significant price changes (3%+ movements)
- Daily price reports (4 times per day)
- Important cryptocurrency news

Usage:
    python main.py          # Start with web dashboard
    python main.py --cli    # Run in CLI mode only
    python main.py --help   # Show help
"""

import sys
import argparse
from bot import EthereumBot
from web_app import app, start_bot_monitoring

def run_cli_mode():
    """Run bot in CLI-only mode"""
    print("🤖 Starting Ethereum Monitoring Bot (CLI Mode)")
    print("=" * 50)
    
    try:
        bot = EthereumBot()
        bot.run_once())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

def run_web_mode():
    """Run bot with web dashboard"""
    print("🌐 Starting Ethereum Monitoring Bot with Web Dashboard")
    print("=" * 50)
    
    try:
        # Auto-start bot monitoring
        start_bot_monitoring()
        print("🚀 Bot monitoring started in background")
        print("🌐 Web dashboard available at: http://localhost:5000")
        print("📊 Access the dashboard to monitor bot status and control operations")
        print("⏹️  Press Ctrl+C to stop")
        
        # Start Flask web server
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ethereum Monitoring Bot with Telegram notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py              # Start with web dashboard (default)
    python main.py --cli        # Run in command-line mode only
    
The bot will:
    • Monitor ETH price every 60 minutes
    • Send alerts for 3%+ price changes
    • Send daily reports at 8AM, 12PM, 4PM, 8PM
    • Send important crypto news updates (if API key configured)
        """
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode without web dashboard'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Ethereum Bot v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Check environment variables
    try:
        from config import Config
        config = Config()
        print(f"✅ Configuration loaded successfully")
        print(f"📱 Telegram User: @{config.telegram_user_id}")
        print(f"📊 Price Threshold: {config.price_change_threshold}%")
        print(f"📰 News Updates: {'Enabled' if config.has_cryptopanic_key else 'Disabled'}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set:")
        print("  - TELEGRAM_TOKEN")
        print("  - TELEGRAM_USER_ID")
        print("  - CRYPTOPANIC_API_KEY (optional)")
        sys.exit(1)
    
    # Run in appropriate mode
    if args.cli:
        run_cli_mode()
    else:
        run_web_mode()

if __name__ == '__main__':
    main()
