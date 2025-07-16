# Ethereum Monitoring Bot

## Overview

This is a Python-based Telegram bot that monitors Ethereum prices and sends notifications for significant price changes, daily reports, and cryptocurrency news. The bot features both a CLI interface and a web dashboard for monitoring and control.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components
- **Bot Engine** (`bot.py`): Main monitoring logic and Telegram integration
- **Configuration** (`config.py`): Centralized configuration management
- **Data Storage** (`data_store.py`): File-based persistence layer
- **Task Scheduling** (`scheduler.py`): Background task management
- **Web Interface** (`web_app.py`): Flask-based dashboard
- **Entry Point** (`main.py`): Application launcher with CLI/web modes

### Architecture Pattern
- **Monolithic structure** with modular components
- **Service-oriented design** where each module has specific responsibilities
- **Event-driven monitoring** using periodic tasks and schedulers
- **Dual interface approach** supporting both CLI and web operations

## Key Components

### 1. Bot Engine (EthereumBot)
- Fetches Ethereum prices from CoinGecko API
- Monitors price changes and sends alerts for 3%+ movements
- Integrates with Telegram Bot API for notifications
- Handles news updates from CryptoPanic API
- Manages daily reporting schedule

### 2. Data Persistence
- **File-based storage** using JSON format
- Stores bot state, price history, and configuration
- Tracks statistics like total alerts sent and last operations
- Simple key-value interface for data access

### 3. Task Scheduler
- **Custom scheduling system** for periodic and time-based tasks
- Supports periodic tasks (price monitoring every 30 seconds)
- Handles daily tasks (reports at specific hours)
- Thread-safe background execution

### 4. Web Dashboard
- **Flask-based web interface** for monitoring and control
- Real-time bot status and statistics
- Manual control buttons for testing and operations
- Bootstrap-based responsive UI

### 5. Configuration Management
- **Environment variable based** configuration
- Validation for required settings
- Centralized API endpoints and thresholds
- Support for optional features (news requires API key)

## Data Flow

1. **Price Monitoring Flow**:
   - Bot fetches current ETH price from CoinGecko
   - Compares with stored previous price
   - Calculates percentage change
   - Sends Telegram alert if change exceeds threshold
   - Updates stored price data

2. **News Monitoring Flow**:
   - Periodically checks CryptoPanic API for important ETH news
   - Filters by timestamp to avoid duplicates
   - Sends formatted news updates via Telegram
   - Updates last news check timestamp

3. **Daily Reporting Flow**:
   - Scheduled tasks trigger at configured hours
   - Generates summary with current price and 24h change
   - Sends comprehensive report via Telegram
   - Records report generation time

4. **Web Dashboard Flow**:
   - Flask serves dashboard interface
   - JavaScript polls for real-time updates
   - Provides controls for manual operations
   - Displays bot status and statistics

## External Dependencies

### APIs
- **CoinGecko API**: Free cryptocurrency price data
- **Telegram Bot API**: Message sending and bot management
- **CryptoPanic API**: Cryptocurrency news aggregation (optional)

### Libraries
- **requests**: HTTP API communication
- **python-telegram-bot**: Telegram integration
- **Flask**: Web framework for dashboard
- **threading**: Background task execution
- **json**: Data serialization

### Environment Variables
- `TELEGRAM_TOKEN`: Required for bot authentication
- `TELEGRAM_USER_ID`: Target user for notifications
- `CRYPTOPANIC_API_KEY`: Optional for news features

## Deployment Strategy

### Development Mode
- Direct Python execution with `python main.py`
- CLI mode available with `--cli` flag
- Web dashboard on localhost:5000

### Production Considerations
- **Process Management**: Requires process manager (systemd, supervisor)
- **Data Persistence**: JSON file storage in writable directory
- **Error Handling**: Basic error logging and recovery
- **Security**: Environment variables for sensitive tokens
- **Monitoring**: Web dashboard provides basic monitoring

### Scalability Limitations
- **Single-user design**: Hardcoded for one Telegram user
- **File-based storage**: Not suitable for high-volume data
- **No database**: Limited to simple key-value persistence
- **Memory usage**: All data kept in memory between saves

### Infrastructure Requirements
- Python 3.x environment
- Internet access for API calls
- Writable filesystem for data persistence
- Port 5000 available for web dashboard (optional)

## Configuration Notes

The bot is designed for personal use with configurable thresholds:
- **Price change threshold**: 3% default (configurable)
- **Check interval**: 30 seconds default
- **Daily reports**: 4 times per day (8, 12, 16, 20 hours)
- **News check interval**: 5 minutes

The modular design allows easy extension for additional cryptocurrencies or notification channels.