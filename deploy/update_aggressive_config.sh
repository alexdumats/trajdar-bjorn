#!/bin/bash

# AI Trading System - Aggressive Configuration Update Script
# Updates system configuration for more aggressive trading parameters

set -e

echo "📈 Updating to Aggressive Trading Configuration..."

# Environment Configuration
TRADING_ENV=production
LOG_LEVEL=INFO

# System Paths
CONFIG_DIR=/opt/ai-trading-system/config
LOG_DIR=/opt/ai-trading-system/logs
BACKUP_DIR=/opt/ai-trading-system/backups
PID_DIR=/opt/ai-trading-system/pids

# Service Configuration
ORCHESTRATOR_PORT=8001
PORTFOLIO_PORT=8002
RISK_MANAGER_PORT=8003
TRADE_EXECUTOR_PORT=8004
MARKET_ANALYST_PORT=8005
NOTIFICATION_PORT=8006
PARAMETER_OPTIMIZER_PORT=8007

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_trading_system
DB_USER=trader
DB_PASSWORD=secure_password_here
DB_PATH=/opt/ai-trading-system/database/paper_trading.db

# API Configuration
BINANCE_API_URL=https://api.binance.com/api/v3
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BINANCE_BASE_URL=https://testnet.binance.vision
BINANCE_TESTNET=true

# Slack Integration
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
SLACK_TRADING_ALERTS_CHANNEL=trading-alerts
SLACK_GENERAL_CHANNEL=general

# Risk Management - Aggressive
LOSS_THRESHOLD=0.20
MIN_TRADES_FOR_OPTIMIZATION=5
RISK_MULTIPLIER=2.0
MAX_POSITION_SIZE=0.15
DAILY_LOSS_LIMIT=0.10

# Trading Parameters - Aggressive
RSI_OVERSOLD=25
RSI_OVERBOUGHT=75
RSI_PERIOD=12
VOLUME_THRESHOLD=1.5
PRICE_CHANGE_THRESHOLD=0.025
STOP_LOSS_PERCENTAGE=0.08
TAKE_PROFIT_PERCENTAGE=0.12
OPTIMIZATION_FREQUENCY=300

# Monitoring
HEALTH_CHECK_INTERVAL=30
METRICS_COLLECTION_INTERVAL=60
ALERT_THRESHOLD_CPU=85
ALERT_THRESHOLD_MEMORY=90

# Create configuration file
cat > $CONFIG_DIR/aggressive_config.yaml << EOF
# Aggressive Trading Configuration
trading:
  mode: aggressive
  risk_tolerance: high
  optimization_frequency: $OPTIMIZATION_FREQUENCY
  
parameters:
  rsi:
    oversold: $RSI_OVERSOLD
    overbought: $RSI_OVERBOUGHT
    period: $RSI_PERIOD
  
  risk:
    stop_loss: $STOP_LOSS_PERCENTAGE
    take_profit: $TAKE_PROFIT_PERCENTAGE
    max_position_size: $MAX_POSITION_SIZE
    daily_loss_limit: $DAILY_LOSS_LIMIT
    
  thresholds:
    volume: $VOLUME_THRESHOLD
    price_change: $PRICE_CHANGE_THRESHOLD

api:
  binance:
    url: $BINANCE_API_URL
    testnet: $BINANCE_TESTNET
    
slack:
  alerts_channel: $SLACK_TRADING_ALERTS_CHANNEL
  general_channel: $SLACK_GENERAL_CHANNEL

monitoring:
  health_check_interval: $HEALTH_CHECK_INTERVAL
  metrics_interval: $METRICS_COLLECTION_INTERVAL
EOF

echo "✅ Aggressive configuration updated successfully!"
echo "📊 Key changes:"
echo "   - RSI thresholds: $RSI_OVERSOLD/$RSI_OVERBOUGHT"
echo "   - Stop loss: $STOP_LOSS_PERCENTAGE%"
echo "   - Take profit: $TAKE_PROFIT_PERCENTAGE%"
echo "   - Max position size: $MAX_POSITION_SIZE%"
echo "   - Optimization frequency: ${OPTIMIZATION_FREQUENCY}s"

# Restart services to apply new configuration
echo "🔄 Restarting services..."
systemctl restart ai-trading-orchestrator
systemctl restart ai-trading-portfolio
systemctl restart ai-trading-risk-manager
systemctl restart ai-trading-executor

echo "🚀 System updated to aggressive configuration!"