"""
Paper Trading Engine for Crypto Trading Bot
Simulates trading with real market data from Binance

Changelog:
- Initial documentation of file structure and main components.
- Validation Step: Confirmed numpy is installed, but Pylance still reports "Import 'numpy' could not be resolved."
- Outstanding Issue: Numpy import unresolved by Pylance; may require VSCode interpreter or environment configuration.
- Contains: PaperTradingEngine class with methods for database initialization, price fetching, RSI calculation, portfolio management, trade execution, position management, signal generation, and performance summary.
- Entry point for testing the engine in __main__.
"""

import sqlite3
import requests
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import os
import sentry_sdk

# Import centralized configuration manager
try:
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.config_manager import get_config

class PaperTradingEngine:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use database directory in current working directory
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(current_dir, "database")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "paper_trading.db")
        else:
            self.db_path = db_path
            
        # Load centralized configuration
        self.config = get_config()
        risk_config = self.config.get_risk_management_config()
        portfolio_config = self.config.get_portfolio_config()
        
        self.binance_api = os.getenv("BINANCE_API_URL", "https://api.binance.com/api/v3")
        self.symbol = os.getenv("TRADING_SYMBOL", "BTCUSDC")
        
        # Risk management parameters from centralized config
        self.position_size_pct = risk_config['max_position_size']
        self.stop_loss_pct = risk_config['stop_loss_pct']
        self.take_profit_pct = risk_config['take_profit_pct']
        self.starting_balance = portfolio_config['starting_balance']
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create portfolio table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                id INTEGER PRIMARY KEY,
                usdc_balance REAL NOT NULL,
                btc_balance REAL NOT NULL,
                total_value REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                signal_type TEXT,
                rsi_value REAL,
                status TEXT DEFAULT 'FILLED',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        # Initialize portfolio if doesn't exist
        cursor.execute("SELECT COUNT(*) FROM paper_portfolio WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO paper_portfolio (id, usdc_balance, btc_balance, total_value)
                VALUES (1, ?, 0.0, ?)
            """, (self.starting_balance, self.starting_balance))
        
        conn.commit()
        conn.close()
        print(f"Database initialized at: {self.db_path}")
        
    def get_current_price(self) -> Optional[float]:
        """Get current BTC/USDT price from Binance"""
        url = f"{self.binance_api}/ticker/price"
        try:
            params = {"symbol": self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            error_msg = f"Error fetching price for {self.symbol}: {e}"
            print(error_msg)
            # Capture exception in Sentry with additional context
            sentry_sdk.capture_exception(e)
            sentry_sdk.set_context("api_request", {
                "url": url,
                "symbol": self.symbol,
                "method": "GET"
            })
            return None
    
    def get_klines(self, interval: str = "1m", limit: int = None) -> List[List]:
        """Get candlestick data from Binance"""
        if limit is None:
            limit = self.config.get_execution_config()['klines_limit']
            
        url = f"{self.binance_api}/klines"
        try:
            params = {
                "symbol": self.symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_msg = f"Error fetching klines for {self.symbol} with interval {interval}: {e}"
            print(error_msg)
            # Capture exception in Sentry with additional context
            sentry_sdk.capture_exception(e)
            sentry_sdk.set_context("api_request", {
                "url": url,
                "symbol": self.symbol,
                "interval": interval,
                "limit": limit,
                "method": "GET"
            })
            return []
    
    def calculate_rsi(self, prices: List[float], period: int = None) -> float:
        if period is None:
            period = self.config.get_rsi_config()['period']
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return self.config.get_rsi_config()['neutral_value']  # Neutral RSI if not enough data
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def get_portfolio(self) -> Dict:
        """Get current portfolio balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT usdc_balance, btc_balance, total_value FROM paper_portfolio WHERE id = 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "usdc_balance": result[0],
                "btc_balance": result[1],
                "total_value": result[2]
            }
        return {"usdc_balance": self.starting_balance, "btc_balance": 0.0, "total_value": self.starting_balance}
    
    def update_portfolio(self, usdc_balance: float, btc_balance: float, total_value: float):
        """Update portfolio balances"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE paper_portfolio 
            SET usdc_balance = ?, btc_balance = ?, total_value = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE id = 1
        """, (usdc_balance, btc_balance, total_value))
        conn.commit()
        conn.close()
    
    def execute_paper_trade(self, side: str, signal_type: str, rsi_value: float) -> Dict:
        """Execute a paper trade"""
        try:
            # Create a transaction for performance monitoring
            with sentry_sdk.start_transaction(op="trade", name=f"{side}_trade_{self.symbol}") as transaction:
                # Add span for getting current price
                with sentry_sdk.start_span(op="api.request", description=f"Get {self.symbol} price") as span:
                    current_price = self.get_current_price()
                    if current_price:
                        span.set_data("price", current_price)
                    
                if not current_price:
                    error_msg = "Could not fetch current price"
                    sentry_sdk.capture_message(error_msg, level="error")
                    return {"success": False, "error": error_msg}
            
            # Add span for getting portfolio
            with sentry_sdk.start_span(op="db.query", description="Get portfolio") as span:
                portfolio = self.get_portfolio()
                span.set_data("portfolio", portfolio)
            
            trade_id = str(uuid.uuid4())[:8]
            
            # Set transaction context for Sentry
            transaction.set_tag("trade_id", trade_id)
            transaction.set_tag("side", side)
            transaction.set_tag("symbol", self.symbol)
            transaction.set_tag("signal_type", signal_type)
            
            sentry_sdk.set_context("trade", {
                "trade_id": trade_id,
                "side": side,
                "symbol": self.symbol,
                "signal_type": signal_type,
                "rsi_value": rsi_value,
                "current_price": current_price
            })
            
            if side == "BUY":
                # Calculate position size based on position size percentage
                trade_amount = portfolio["total_value"] * self.position_size_pct
                
                # Check if we have enough USDC balance
                min_usdc_balance = self.config.get_risk_management_config().get('min_usdc_balance', 0)
                if trade_amount > portfolio["usdc_balance"] or portfolio["usdc_balance"] < min_usdc_balance:
                    error_msg = f"Insufficient USDC balance: {portfolio['usdc_balance']}, needed: {trade_amount}"
                    sentry_sdk.capture_message(error_msg, level="warning")
                    return {"success": False, "error": "Insufficient USDC balance"}
                
                quantity = trade_amount / current_price
                new_usdc = portfolio["usdc_balance"] - trade_amount
                new_btc = portfolio["btc_balance"] + quantity
                
                # Set stop loss and take profit
                stop_loss = current_price * (1 - self.stop_loss_pct)
                take_profit = current_price * (1 + self.take_profit_pct)
                
                # Record position
                self._record_position("BUY", quantity, current_price, stop_loss, take_profit)
                
            else:  # SELL
                if portfolio["btc_balance"] <= 0:
                    error_msg = f"No BTC to sell: current balance = {portfolio['btc_balance']}"
                    sentry_sdk.capture_message(error_msg, level="warning")
                    return {"success": False, "error": "No BTC to sell"}
                
                quantity = portfolio["btc_balance"]
                trade_amount = quantity * current_price
                new_usdc = portfolio["usdc_balance"] + trade_amount
                new_btc = 0.0
                
                # Close any open positions
                self._close_positions()
            
            # Update portfolio
            new_total = new_usdc + (new_btc * current_price)
            with sentry_sdk.start_span(op="db.write", description="Update portfolio") as span:
                self.update_portfolio(new_usdc, new_btc, new_total)
                span.set_data("new_portfolio", {
                    "usdc_balance": new_usdc,
                    "btc_balance": new_btc,
                    "total_value": new_total
                })
            
            # Record trade
            with sentry_sdk.start_span(op="db.write", description="Record trade") as span:
                self._record_trade(trade_id, side, quantity, current_price, trade_amount, signal_type, rsi_value, 'FILLED')
                span.set_data("trade_details", {
                    "trade_id": trade_id,
                    "side": side,
                    "quantity": quantity,
                    "price": current_price,
                    "total": trade_amount
                })
            
            # Log successful trade to Sentry
            sentry_sdk.capture_message(
                f"Trade executed: {side} {quantity} {self.symbol} at {current_price}",
                level="info"
            )
            
            return {
                "success": True,
                "trade_id": trade_id,
                "side": side,
                "quantity": quantity,
                "price": current_price,
                "total": trade_amount,
                "new_portfolio": self.get_portfolio()
            }
            
        except Exception as e:
            error_msg = f"Error executing {side} trade: {e}"
            print(error_msg)
            sentry_sdk.capture_exception(e)
            return {"success": False, "error": str(e)}
    
    def _record_trade(self, trade_id: str, side: str, quantity: float, price: float, total: float, signal_type: str, rsi_value: float, status: str = 'FILLED'):
        """Record trade in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO paper_trades (trade_id, symbol, side, quantity, price, total, signal_type, rsi_value, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (trade_id, self.symbol, side, quantity, price, total, signal_type, rsi_value, status))
        conn.commit()
        conn.close()
    
    def _record_position(self, side: str, quantity: float, entry_price: float, stop_loss: float, take_profit: float):
        """Record open position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO paper_positions (symbol, side, quantity, entry_price, stop_loss, take_profit, status)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
        """, (self.symbol, side, quantity, entry_price, stop_loss, take_profit))
        conn.commit()
        conn.close()
    
    def _close_positions(self):
        """Close all open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE paper_positions SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP WHERE status = 'OPEN'")
        conn.commit()
        conn.close()
    
    def check_stop_loss_take_profit(self) -> List[Dict]:
        """Check if any open positions hit stop loss or take profit"""
        try:
            # Create a transaction for performance monitoring
            with sentry_sdk.start_transaction(op="check_sl_tp", name="check_stop_loss_take_profit") as transaction:
                # Add span for getting current price
                with sentry_sdk.start_span(op="api.request", description=f"Get {self.symbol} price") as span:
                    current_price = self.get_current_price()
                    if current_price:
                        span.set_data("price", current_price)
                        transaction.set_tag("current_price", str(current_price))
                
                if not current_price:
                    sentry_sdk.capture_message("Failed to check stop loss/take profit: Could not fetch current price", level="error")
                    return []
                
                # Add span for querying open positions
                with sentry_sdk.start_span(op="db.query", description="Get open positions") as span:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, side, quantity, entry_price, stop_loss, take_profit
                        FROM paper_positions WHERE status = 'OPEN'
                    """)
                    positions = cursor.fetchall()
                    span.set_data("positions_count", len(positions))
                    transaction.set_tag("open_positions", str(len(positions)))
            
            triggered_trades = []
            
            for pos in positions:
                pos_id, side, quantity, entry_price, stop_loss, take_profit = pos
                
                # Set position context for Sentry
                sentry_sdk.set_context("position", {
                    "id": pos_id,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "current_price": current_price
                })
                
                if side == "BUY":
                    if current_price <= stop_loss:
                        # Stop loss triggered
                        sentry_sdk.capture_message(
                            f"Stop loss triggered for position {pos_id}: current price {current_price} <= stop loss {stop_loss}",
                            level="info"
                        )
                        trade_result = self.execute_paper_trade("SELL", "STOP_LOSS", 0)
                        triggered_trades.append({"type": "STOP_LOSS", "price": current_price, "trade": trade_result})
                    elif current_price >= take_profit:
                        # Take profit triggered
                        sentry_sdk.capture_message(
                            f"Take profit triggered for position {pos_id}: current price {current_price} >= take profit {take_profit}",
                            level="info"
                        )
                        trade_result = self.execute_paper_trade("SELL", "TAKE_PROFIT", 0)
                        triggered_trades.append({"type": "TAKE_PROFIT", "price": current_price, "trade": trade_result})
            
            conn.close()
            return triggered_trades
            
        except Exception as e:
            error_msg = f"Error checking stop loss/take profit: {e}"
            print(error_msg)
            sentry_sdk.capture_exception(e)
            return []
    
    def get_trading_signal(self) -> Optional[Dict]:
        """Generate trading signal based on RSI"""
        try:
            # Create a transaction for performance monitoring
            with sentry_sdk.start_transaction(op="signal", name=f"trading_signal_{self.symbol}") as transaction:
                execution_config = self.config.get_execution_config()
                
                # Add span for getting klines
                with sentry_sdk.start_span(op="api.request", description=f"Get {self.symbol} klines") as span:
                    klines = self.get_klines(interval="1m", limit=execution_config['price_history_limit'])
                    span.set_data("klines_count", len(klines) if klines else 0)
                
                if not klines:
                    sentry_sdk.capture_message("Failed to generate trading signal: Could not fetch klines", level="error")
                    return None
                
                # Extract closing prices and calculate RSI
                with sentry_sdk.start_span(op="calculation", description="Calculate RSI") as span:
                    closes = [float(kline[4]) for kline in klines]
                    rsi = self.calculate_rsi(closes)
                    span.set_data("rsi", rsi)
                
                # Add span for getting current price
                with sentry_sdk.start_span(op="api.request", description=f"Get {self.symbol} price") as span:
                    current_price = self.get_current_price()
                    if current_price:
                        span.set_data("price", current_price)
            
            if not current_price:
                sentry_sdk.capture_message("Failed to generate trading signal: Could not fetch current price", level="error")
                return None
            
            portfolio = self.get_portfolio()
            
            signal = {
                "timestamp": datetime.now().isoformat(),
                "price": current_price,
                "rsi": rsi,
                "signal": None,
                "reason": ""
            }
            
            # Set signal context for Sentry
            sentry_sdk.set_context("signal_data", {
                "rsi": rsi,
                "price": current_price,
                "usdc_balance": portfolio["usdc_balance"],
                "btc_balance": portfolio["btc_balance"],
                "timestamp": signal["timestamp"]
            })
            
            # Generate signals
            rsi_config = self.config.get_rsi_config()
            risk_config = self.config.get_risk_management_config()
            
            if rsi < rsi_config['oversold_threshold'] and portfolio["usdc_balance"] > risk_config['min_usdc_balance']:  # Oversold and have USDC
                signal["signal"] = "BUY"
                signal["reason"] = f"RSI oversold at {rsi:.2f}"
                sentry_sdk.capture_message(f"BUY signal generated: RSI oversold at {rsi:.2f}", level="info")
            elif rsi > rsi_config['overbought_threshold'] and portfolio["btc_balance"] > 0:  # Overbought and have BTC
                signal["signal"] = "SELL"
                signal["reason"] = f"RSI overbought at {rsi:.2f}"
                sentry_sdk.capture_message(f"SELL signal generated: RSI overbought at {rsi:.2f}", level="info")
            else:
                signal["reason"] = f"RSI neutral at {rsi:.2f}, no signal"
            
            return signal
            
        except Exception as e:
            error_msg = f"Error generating trading signal: {e}"
            print(error_msg)
            sentry_sdk.capture_exception(e)
            return None
    
    def get_performance_summary(self) -> Dict:
        """Get trading performance summary"""
        portfolio = self.get_portfolio()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total trades
        cursor.execute("SELECT COUNT(*) FROM paper_trades")
        total_trades = cursor.fetchone()[0]
        
        # Get recent trades
        cursor.execute("SELECT * FROM paper_trades ORDER BY timestamp DESC LIMIT 10")
        recent_trades = cursor.fetchall()
        
        conn.close()
        
        initial_balance = self.starting_balance
        current_balance = portfolio["total_value"]
        pnl = current_balance - initial_balance
        pnl_pct = (pnl / initial_balance) * 100
        
        return {
            "portfolio": portfolio,
            "initial_balance": initial_balance,
            "current_balance": current_balance,
            "pnl": pnl,
            "pnl_percentage": pnl_pct,
            "total_trades": total_trades,
            "recent_trades": recent_trades
        }

if __name__ == "__main__":
    # Initialize Sentry
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn != "https://examplePublicKey@o0.ingest.sentry.io/0":
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            release=f"paper-trading-engine@{os.getenv('SYSTEM_VERSION', '1.0.0')}",
        )
        print("✅ Sentry initialized for error monitoring")
    
    # Test the engine
    try:
        engine = PaperTradingEngine()
        
        print("Paper Trading Engine initialized!")
        print("Current portfolio:", engine.get_portfolio())
        print("Current BTC price:", engine.get_current_price())
        
        signal = engine.get_trading_signal()
        print("Trading signal:", signal)
        
        performance = engine.get_performance_summary()
        print("Performance summary:", performance)
        
        # Test Sentry error reporting with a deliberate error if SENTRY_TEST_ERROR is set
        if os.getenv("SENTRY_TEST_ERROR", "false").lower() == "true":
            print("Testing Sentry error reporting...")
            raise Exception("This is a test error to verify Sentry integration")
            
    except Exception as e:
        print(f"❌ Error running paper trading engine: {e}")
        sentry_sdk.capture_exception(e)
        raise
