#!/bin/bash
# AI Trading System Live Monitor
# Run this to continuously monitor your trading system

SERVER_IP="135.181.164.232"
PASSWORD="CQGT8hcWLZCV8G"

echo "🚀 AI TRADING SYSTEM - LIVE MONITOR"
echo "======================================"
echo "Server: $SERVER_IP"
echo "Trading Pairs: BTC/USDC, ETH/USDC, SOL/USDC"
echo "Strategy: Optimized RSI (Period: 7, Stop: 3%, Profit: 8%)"
echo ""

# Function to get current status
get_status() {
    echo "📊 $(date '+%H:%M:%S') - System Status:"
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "
        echo '💼 Portfolio:' && curl -s http://localhost:8001/portfolio | jq '.total_value, .current_btc_price' 2>/dev/null || echo 'Loading...'
        echo '🤖 Orchestration:' && curl -s http://localhost:8000/orchestration-status | jq '.is_running, .cycle_count' 2>/dev/null || echo 'Loading...'
        echo '⚙️ Optimizer:' && curl -s http://localhost:8006/status | jq '.current_parameters.execution_interval' 2>/dev/null || echo 'Loading...'
    "
    echo "----------------------------------------"
}

# Main monitoring loop
echo "Starting continuous monitoring (Ctrl+C to stop)..."
echo ""

while true; do
    get_status
    sleep 30
done