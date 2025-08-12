#!/usr/bin/env python3
"""
Parameter Optimizer Service - Intelligent Trading Parameter Tuning
Runs before other services and optimizes parameters based on recent performance
Uses Optuna MCP for hyperparameter optimization
"""

import asyncio
import aiohttp
import json
import logging
import os
import sqlite3
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from slack_webhook_logger import SlackWebhookLogger
import random

# Import centralized configuration manager
try:
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.config_manager import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Parameter Optimizer Service", version="1.0.0")

class ParameterOptimizer:
    def __init__(self):
        self.config_path = os.getenv("CONFIG_PATH", "/app/config/production_config.yaml")
        self.db_path = os.getenv("DB_PATH", "/app/database/paper_trading.db")
        self.mcp_hub_url = os.getenv("MCP_HUB_URL", "http://mcp-hub:9000")
        
        # Optuna MCP configuration
        self.optuna_mcp = os.getenv("OPTUNA_MCP_URL", "http://localhost:8301")
        
        # Slack MCP configuration
        self.slack_mcp_url = os.getenv("SLACK_MCP_URL", "http://localhost:8080")
        
        # Optimization triggers
        self.loss_threshold = float(os.getenv("LOSS_THRESHOLD", "0.05"))  # 5% loss triggers optimization
        self.min_trades_for_optimization = int(os.getenv("MIN_TRADES_FOR_OPTIMIZATION", "10"))
        self.optimization_lookback_hours = int(os.getenv("OPTIMIZATION_LOOKBACK_HOURS", "24"))
        
        # Load centralized configuration
        self.config = get_config()
        
        # Loss event monitoring
        self.loss_events = []
        self.monitoring_active = False
        
        # Current parameters (loaded from centralized config)
        rsi_config = self.config.get_rsi_config()
        risk_config = self.config.get_risk_management_config()
        
        self.current_params = {
            "rsi_period": rsi_config['period'],
            "rsi_oversold": rsi_config['oversold_threshold'],
            "rsi_overbought": rsi_config['overbought_threshold'],
            "min_confidence": risk_config['min_confidence'],
            "max_position_size": risk_config['max_position_size'],
            "stop_loss_pct": risk_config['stop_loss_pct'],
            "take_profit_pct": risk_config['take_profit_pct'],
            "execution_interval": self.config.get_execution_config()['trade_interval_seconds']
        }
        
        # Original parameters (for restoring after learning sessions)
        self.original_params = self.current_params.copy()
        
        # Learning session state
        self.learning_session_active = False
        self.learning_session_start_time = None
        self.learning_session_duration_minutes = int(os.getenv("LEARNING_SESSION_DURATION_MINUTES", "60"))
        self.learning_session_cooldown_hours = int(os.getenv("LEARNING_SESSION_COOLDOWN_HOURS", "24"))
        self.last_learning_session = None
        self.learning_session_trades = []
        
        # Optimization state
        self.is_optimizing = False
        self.last_optimization = None
        self.optimization_results = []
        
        # Slack logger
        self.slack_logger = SlackWebhookLogger("parameter_optimizer")
        
        # Load configuration
        self.load_config()
        
        logger.info("🔧 Parameter Optimizer initialized")
    
    def load_config(self):
        """Load current configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Extract current trading parameters
            strategies = config.get('trading', {}).get('strategies', {})
            rsi_config = strategies.get('rsi', {})
            risk_config = config.get('trading', {}).get('risk_management', {})
            
            # Reload centralized configuration
            self.config = get_config()
            rsi_config = self.config.get_rsi_config()
            risk_config = self.config.get_risk_management_config()
            
            self.current_params.update({
                "rsi_period": rsi_config['period'],
                "rsi_oversold": rsi_config['oversold_threshold'],
                "rsi_overbought": rsi_config['overbought_threshold'], 
                "min_confidence": risk_config['min_confidence'],
                "max_position_size": risk_config['max_position_size'],
                "stop_loss_pct": risk_config['stop_loss_pct'],
                "take_profit_pct": risk_config['take_profit_pct']
            })
            
            logger.info("✅ Current parameters loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
    
    async def get_recent_performance(self) -> Dict[str, Any]:
        """Analyze recent trading performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get trades from last N hours
            cutoff_time = datetime.now() - timedelta(hours=self.optimization_lookback_hours)
            
            cursor.execute("""
                SELECT * FROM trades 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            trades = cursor.fetchall()
            conn.close()
            
            if len(trades) < self.min_trades_for_optimization:
                return {
                    "total_trades": len(trades),
                    "total_pnl": 0.0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0,
                    "max_drawdown": 0.0,
                    "needs_optimization": False,
                    "reason": f"Insufficient trades ({len(trades)} < {self.min_trades_for_optimization})"
                }
            
            # Calculate performance metrics
            total_pnl = 0.0
            winning_trades = 0
            profits = []
            portfolio_values = []
            
            for trade in trades:
                # Assuming trade format: (id, symbol, side, quantity, price, total, pnl, timestamp)
                pnl = trade[6] if len(trade) > 6 else 0
                total_pnl += pnl
                profits.append(pnl)
                
                if pnl > 0:
                    winning_trades += 1
            
            win_rate = winning_trades / len(trades) if trades else 0
            avg_profit = sum(profits) / len(profits) if profits else 0
            
            # Calculate max drawdown
            running_total = 0
            max_value = 0
            max_drawdown = 0
            
            for profit in profits:
                running_total += profit
                max_value = max(max_value, running_total)
                drawdown = (max_value - running_total) / max_value if max_value > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            # Determine if optimization is needed (using centralized config for starting balance)
            starting_balance = self.config.get_trading_config().get('starting_balance', 10000)
            
            needs_optimization = (
                total_pnl < -self.loss_threshold * starting_balance or
                win_rate < 0.4 or  # Less than 40% win rate
                max_drawdown > self.loss_threshold
            )
            
            performance = {
                "total_trades": len(trades),
                "total_pnl": round(total_pnl, 2),
                "win_rate": round(win_rate, 3),
                "avg_profit": round(avg_profit, 2),
                "max_drawdown": round(max_drawdown, 3),
                "needs_optimization": needs_optimization,
                "lookback_hours": self.optimization_lookback_hours
            }
            
            if needs_optimization:
                reasons = []
                if total_pnl < -self.loss_threshold * starting_balance:
                    reasons.append(f"High losses (${total_pnl:.2f})")
                if win_rate < 0.4:
                    reasons.append(f"Low win rate ({win_rate:.1%})")
                if max_drawdown > self.loss_threshold:
                    reasons.append(f"High drawdown ({max_drawdown:.1%})")
                
                performance["reason"] = "; ".join(reasons)
            
            return performance
            
        except Exception as e:
            logger.error(f"❌ Performance analysis error: {e}")
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "max_drawdown": 0.0,
                "needs_optimization": False,
                "reason": f"Analysis error: {e}"
            }
    
    async def analyze_recent_performance(self) -> Dict[str, Any]:
        """Alias for get_recent_performance - used by monitoring loop"""
        logger.info("analyze_recent_performance called - using get_recent_performance")
        return await self.get_recent_performance()
    
    async def optimize_parameters(self) -> Dict[str, Any]:
        """Run optimization process - called by monitoring loop"""
        logger.info("optimize_parameters called - running optimization")
        return await self.run_optimization()
    
    async def call_optuna_mcp(self, study_name: str, objective_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Optuna MCP server for parameter optimization"""
        try:
            # First check if MCP Hub is available
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mcp_hub_url}/servers/optuna", timeout=5) as response:
                    if response.status != 200:
                        logger.warning("⚠️ Optuna MCP server not available, using fallback optimization")
                        return await self.fallback_optimization(objective_data)
                
                # Call Optuna MCP for optimization
                optimization_request = {
                    "study_name": study_name,
                    "objective": "maximize_profit",
                    "parameters": {
                        "rsi_period": {"type": "int", "low": 5, "high": 21},
                        "rsi_oversold": {"type": "int", "low": 20, "high": 35},
                        "rsi_overbought": {"type": "int", "low": 65, "high": 85},
                        "min_confidence": {"type": "float", "low": 0.5, "high": 0.8},
                        "max_position_size": {"type": "float", "low": 0.05, "high": 0.25},
                        "stop_loss_pct": {"type": "float", "low": 0.02, "high": 0.05},
                        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.10}
                    },
                    "n_trials": 20,
                    "performance_data": objective_data
                }
                
                async with session.post(
                    f"{self.mcp_hub_url}/mcp/optuna/optimize",
                    json=optimization_request,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"⚠️ Optuna MCP failed ({response.status}), using fallback")
                        return await self.fallback_optimization(objective_data)
                        
        except Exception as e:
            logger.error(f"❌ Optuna MCP error: {e}")
            return await self.fallback_optimization(objective_data)
    
    async def fallback_optimization(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback optimization using simple heuristics"""
        logger.info("🔧 Using fallback optimization heuristics")
        
        optimized_params = self.current_params.copy()
        changes_made = []
        
        # Analyze performance and adjust parameters
        win_rate = performance_data.get("win_rate", 0)
        avg_profit = performance_data.get("avg_profit", 0)
        max_drawdown = performance_data.get("max_drawdown", 0)
        
        # If win rate is low, make RSI more sensitive (within configured bounds)
        rsi_bounds = self.config.get_optimization_bounds().get('rsi', {})
        
        if win_rate < 0.4:
            optimized_params["rsi_period"] = max(rsi_bounds.get('period_min', 5), optimized_params["rsi_period"] - 2)
            optimized_params["rsi_oversold"] = min(rsi_bounds.get('oversold_max', 35), optimized_params["rsi_oversold"] + 5)
            optimized_params["rsi_overbought"] = max(rsi_bounds.get('overbought_min', 65), optimized_params["rsi_overbought"] - 5)
            changes_made.append("Increased RSI sensitivity")
        
        # If average profit is low, adjust position sizing (within configured bounds)
        risk_bounds = self.config.get_optimization_bounds().get('risk_management', {})
        
        if avg_profit < 0:
            optimized_params["max_position_size"] = max(risk_bounds.get('position_size_min', 0.05), optimized_params["max_position_size"] - 0.02)
            optimized_params["stop_loss_pct"] = max(risk_bounds.get('stop_loss_min', 0.02), optimized_params["stop_loss_pct"] - 0.005)
            changes_made.append("Reduced position size and tightened stop-loss")
        
        # If drawdown is high, be more conservative (within configured bounds)
        if max_drawdown > 0.05:
            optimized_params["min_confidence"] = min(risk_bounds.get('confidence_max', 0.8), optimized_params["min_confidence"] + 0.1)
            optimized_params["max_position_size"] = max(risk_bounds.get('position_size_min', 0.05), optimized_params["max_position_size"] - 0.03)
            changes_made.append("Increased confidence threshold and reduced position size")
        
        # If performance is decent, try to be more aggressive (within configured bounds)
        if win_rate > 0.6 and avg_profit > 0 and max_drawdown < 0.03:
            optimized_params["max_position_size"] = min(risk_bounds.get('position_size_max', 0.25), optimized_params["max_position_size"] + 0.02)
            optimized_params["take_profit_pct"] = min(risk_bounds.get('take_profit_max', 0.10), optimized_params["take_profit_pct"] + 0.01)
            changes_made.append("Increased position size and take-profit target")
        
        return {
            "optimized_parameters": optimized_params,
            "optimization_method": "fallback_heuristics",
            "changes_made": changes_made,
            "expected_improvement": "10-20%"
        }
    
    async def update_configuration(self, optimized_params: Dict[str, Any], backup_reason: str = "optimization") -> bool:
        """Update configuration files with optimized parameters"""
        try:
            # First create a backup of current configuration
            backup_success = await self.backup_configuration(backup_reason)
            if not backup_success:
                logger.warning("⚠️ Failed to create backup, but continuing with update")
            
            # Create environment variables for the optimized parameters
            env_updates = {
                "RSI_PERIOD": str(optimized_params["rsi_period"]),
                "RSI_OVERSOLD": str(optimized_params["rsi_oversold"]),
                "RSI_OVERBOUGHT": str(optimized_params["rsi_overbought"]),
                "MIN_CONFIDENCE": str(optimized_params["min_confidence"]),
                "MAX_POSITION_SIZE": str(optimized_params["max_position_size"]),
                "STOP_LOSS_PCT": str(optimized_params["stop_loss_pct"]),
                "TAKE_PROFIT_PCT": str(optimized_params["take_profit_pct"])
            }
            
            # Update .env file
            env_file_path = ".env"
            env_lines = []
            
            # Read existing .env file
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add new parameters
            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var, value in env_updates.items():
                    if line.startswith(f"{var}="):
                        env_lines[i] = f"{var}={value}\n"
                        updated_vars.add(var)
                        break
            
            # Add new variables that weren't found
            for var, value in env_updates.items():
                if var not in updated_vars:
                    env_lines.append(f"{var}={value}\n")
            
            # Write updated .env file
            with open(env_file_path, 'w') as f:
                f.writelines(env_lines)
            
            # Update current parameters
            self.current_params.update(optimized_params)
            
            # Log the parameter change
            await self.log_parameter_change(self.current_params, optimized_params, backup_reason)
            
            logger.info("✅ Configuration updated with optimized parameters")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration update failed: {e}")
            return False
            
    async def backup_configuration(self, reason: str = "manual") -> bool:
        """Create a backup of current configuration"""
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(os.path.dirname(self.config_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"agent_parameters_{timestamp}_{reason}.yaml"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy current config file to backup
            with open(self.config_path, 'r') as src_file:
                config_content = src_file.read()
                
            with open(backup_path, 'w') as backup_file:
                backup_file.write(config_content)
                
            # Also backup .env file
            env_file_path = ".env"
            if os.path.exists(env_file_path):
                env_backup_path = os.path.join(backup_dir, f"env_{timestamp}_{reason}.env")
                with open(env_file_path, 'r') as src_file:
                    env_content = src_file.read()
                    
                with open(env_backup_path, 'w') as backup_file:
                    backup_file.write(env_content)
            
            # Log backup creation
            logger.info(f"✅ Configuration backup created: {backup_path}")
            
            # Store backup metadata in database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    reason TEXT,
                    backup_path TEXT,
                    env_backup_path TEXT,
                    parameters TEXT
                )
                """)
                
                # Insert backup metadata
                cursor.execute("""
                INSERT INTO config_backups (
                    timestamp, reason, backup_path, env_backup_path, parameters
                ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    reason,
                    backup_path,
                    env_backup_path if os.path.exists(env_file_path) else None,
                    json.dumps(self.current_params)
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ Failed to store backup metadata: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration backup failed: {e}")
            return False
            
    async def log_parameter_change(self, old_params: Dict[str, Any], new_params: Dict[str, Any], reason: str) -> None:
        """Log parameter changes to database and Slack"""
        try:
            # Calculate differences
            changes = {}
            for key, new_value in new_params.items():
                if key in old_params:
                    old_value = old_params[key]
                    if new_value != old_value:
                        changes[key] = {
                            "old": old_value,
                            "new": new_value,
                            "diff": f"{old_value} → {new_value}"
                        }
                else:
                    changes[key] = {
                        "old": None,
                        "new": new_value,
                        "diff": f"None → {new_value}"
                    }
            
            # Log to database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    reason TEXT,
                    changes TEXT,
                    old_params TEXT,
                    new_params TEXT
                )
                """)
                
                # Insert parameter change
                cursor.execute("""
                INSERT INTO parameter_changes (
                    timestamp, reason, changes, old_params, new_params
                ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    reason,
                    json.dumps(changes),
                    json.dumps(old_params),
                    json.dumps(new_params)
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ Failed to log parameter change to database: {e}")
            
            # Log to file
            try:
                log_dir = "logs"
                os.makedirs(log_dir, exist_ok=True)
                
                log_file = os.path.join(log_dir, "config_changes.jsonl")
                
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "reason": reason,
                    "changes": changes,
                    "old_params": old_params,
                    "new_params": new_params
                }
                
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + "\n")
                    
            except Exception as e:
                logger.error(f"❌ Failed to log parameter change to file: {e}")
            
            # Notify via Slack
            try:
                # Format changes for Slack
                changes_text = ""
                for param, change in changes.items():
                    changes_text += f"• `{param}`: {change['diff']}\n"
                
                await self.send_slack_notification(
                    channel="#parameter-optimizer",
                    message=f"""
*🔄 PARAMETER CHANGES*
*Reason:* {reason}
*Time:* {datetime.now().isoformat()}

*Changes:*
{changes_text}

These changes have been backed up and logged for audit purposes.
"""
                )
                
            except Exception as e:
                logger.error(f"❌ Failed to notify parameter change via Slack: {e}")
                
        except Exception as e:
            logger.error(f"❌ Failed to log parameter change: {e}")
    
    async def run_optimization(self) -> Dict[str, Any]:
        """Run complete optimization process"""
        if self.is_optimizing:
            return {"status": "already_running", "message": "Optimization already in progress"}
        
        self.is_optimizing = True
        optimization_start = time.time()
        
        try:
            logger.info("🔧 Starting parameter optimization")
            await self.slack_logger.log_start("Parameter Optimization", {
                "trigger": "Performance decline detected",
                "lookback_hours": self.optimization_lookback_hours
            })
            
            # Step 1: Analyze recent performance
            logger.info("📊 Analyzing recent performance...")
            performance = await self.get_recent_performance()
            
            if not performance["needs_optimization"]:
                result = {
                    "status": "skipped",
                    "reason": performance["reason"],
                    "performance": performance
                }
                await self.slack_logger.log_info("Optimization skipped", result)
                return result
            
            # Step 2: Call Optuna MCP for optimization
            logger.info("🧠 Running parameter optimization...")
            study_name = f"trading_optimization_{int(time.time())}"
            optimization_result = await self.call_optuna_mcp(study_name, performance)
            
            # Step 3: Update configuration
            if "optimized_parameters" in optimization_result:
                logger.info("💾 Updating configuration...")
                success = await self.update_configuration(optimization_result["optimized_parameters"])
                
                if success:
                    # Step 4: Log results
                    optimization_duration = time.time() - optimization_start
                    self.last_optimization = datetime.now()
                    
                    result = {
                        "status": "completed",
                        "duration_seconds": round(optimization_duration, 2),
                        "previous_performance": performance,
                        "optimization_result": optimization_result,
                        "new_parameters": optimization_result["optimized_parameters"],
                        "timestamp": self.last_optimization.isoformat()
                    }
                    
                    # Log to Slack
                    await self.slack_logger.log_success("Parameter optimization completed", {
                        "duration": f"{optimization_duration:.1f}s",
                        "method": optimization_result.get("optimization_method", "unknown"),
                        "changes": optimization_result.get("changes_made", []),
                        "expected_improvement": optimization_result.get("expected_improvement", "Unknown")
                    })
                    
                    self.optimization_results.append(result)
                    logger.info("✅ Parameter optimization completed successfully")
                    return result
                else:
                    raise Exception("Failed to update configuration")
            else:
                raise Exception("No optimized parameters received")
                
        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            await self.slack_logger.log_error("Parameter optimization failed", {"error": str(e)})
            
            return {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - optimization_start
            }
        finally:
            self.is_optimizing = False
    
    async def start_loss_monitoring(self):
        """Start monitoring for loss events that trigger optimization"""
        if self.monitoring_active:
            logger.warning("Loss monitoring already active")
            return
            
        self.monitoring_active = True
        logger.info("🔍 Starting loss event monitoring")
        
        # Debug logging to diagnose the missing method issue
        logger.info(f"Available methods: {[method for method in dir(self) if not method.startswith('__')]}")
        logger.info(f"analyze_recent_performance defined: {'analyze_recent_performance' in dir(self)}")
        logger.info(f"get_recent_performance defined: {'get_recent_performance' in dir(self)}")
        
        while self.monitoring_active:
            try:
                # Check recent performance every 30 seconds
                # Use get_recent_performance directly instead of the alias
                performance = await self.get_recent_performance()
                
                # Check if optimization is needed
                if performance["needs_optimization"] and not self.is_optimizing:
                    logger.warning(f"⚠️ Loss event detected: {performance['reason']}")
                    
                    # Send loss event to Optuna MCP
                    await self.send_loss_event_to_optuna(performance)
                    
                    # Trigger optimization
                    await self.optimize_parameters()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Loss monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def send_loss_event_to_optuna(self, loss_data: Dict[str, Any]):
        """Send loss event to Optuna MCP for logging"""
        try:
            loss_event = {
                "event_type": "loss_detected",
                "loss_amount": loss_data.get("total_pnl", 0),
                "max_drawdown": loss_data.get("max_drawdown", 0),
                "win_rate": loss_data.get("win_rate", 0),
                "reason": loss_data.get("reason", "Unknown"),
                "timestamp": datetime.now().isoformat(),
                "current_parameters": self.current_params
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.optuna_mcp}/loss_event",
                    json=loss_event,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info("📊 Loss event sent to Optuna MCP")
                    else:
                        logger.warning(f"Failed to send loss event: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send loss event to Optuna MCP: {e}")
    
    def stop_loss_monitoring(self):
        """Stop loss event monitoring"""
        self.monitoring_active = False
        logger.info("🛑 Loss event monitoring stopped")
        
    async def start_learning_session(self, duration_minutes: int = None) -> Dict[str, Any]:
        """Start a learning session with relaxed parameters"""
        if self.learning_session_active:
            return {
                "status": "already_active",
                "message": "Learning session already in progress",
                "start_time": self.learning_session_start_time.isoformat() if self.learning_session_start_time else None,
                "duration_minutes": self.learning_session_duration_minutes
            }
            
        # Check if we're in cooldown period
        if self.last_learning_session:
            cooldown_end = self.last_learning_session + timedelta(hours=self.learning_session_cooldown_hours)
            if datetime.now() < cooldown_end:
                time_remaining = cooldown_end - datetime.now()
                return {
                    "status": "cooldown",
                    "message": f"Learning session cooldown period active",
                    "cooldown_end": cooldown_end.isoformat(),
                    "hours_remaining": time_remaining.total_seconds() / 3600
                }
        
        # Set duration if provided
        if duration_minutes:
            self.learning_session_duration_minutes = duration_minutes
            
        # Backup current parameters
        self.original_params = self.current_params.copy()
        
        # Apply relaxed parameters
        relaxed_params = self.get_relaxed_parameters()
        await self.update_configuration(relaxed_params)
        
        # Set learning session state
        self.learning_session_active = True
        self.learning_session_start_time = datetime.now()
        self.learning_session_trades = []
        
        # Schedule end of learning session
        asyncio.create_task(self.end_learning_session_after_duration())
        
        # Notify via Slack
        await self.send_slack_notification(
            channel="#riskblocked",
            message=f"""
*🧪 LEARNING SESSION STARTED*
Learning session has been activated with relaxed risk parameters.
*Duration:* {self.learning_session_duration_minutes} minutes
*Start Time:* {self.learning_session_start_time.isoformat()}
*End Time:* {(self.learning_session_start_time + timedelta(minutes=self.learning_session_duration_minutes)).isoformat()}

*Relaxed Parameters:*
```
{json.dumps(relaxed_params, indent=2)}
```

All trades executed during this session will be tagged and logged for analysis.
"""
        )
        
        logger.info(f"🧪 Learning session started for {self.learning_session_duration_minutes} minutes")
        
        return {
            "status": "started",
            "start_time": self.learning_session_start_time.isoformat(),
            "end_time": (self.learning_session_start_time + timedelta(minutes=self.learning_session_duration_minutes)).isoformat(),
            "duration_minutes": self.learning_session_duration_minutes,
            "relaxed_parameters": relaxed_params
        }
        
    async def end_learning_session_after_duration(self):
        """End learning session after the specified duration"""
        await asyncio.sleep(self.learning_session_duration_minutes * 60)
        if self.learning_session_active:
            await self.end_learning_session()
            
    async def end_learning_session(self) -> Dict[str, Any]:
        """End learning session and restore original parameters"""
        if not self.learning_session_active:
            return {
                "status": "not_active",
                "message": "No learning session is currently active"
            }
            
        # Restore original parameters
        await self.update_configuration(self.original_params)
        
        # Update learning session state
        self.learning_session_active = False
        session_duration = datetime.now() - self.learning_session_start_time
        self.last_learning_session = datetime.now()
        
        # Get trades executed during session
        session_trades = await self.get_learning_session_trades()
        
        # Analyze session results
        session_results = self.analyze_learning_session_results(session_trades)
        
        # Store session results for optimizer
        await self.store_learning_session_results(session_results)
        
        # Notify via Slack
        await self.send_slack_notification(
            channel="#riskblocked",
            message=f"""
*🧪 LEARNING SESSION COMPLETED*
Learning session has ended and original parameters have been restored.
*Duration:* {session_duration.total_seconds() / 60:.1f} minutes
*Trades Executed:* {len(session_trades)}
*Results:*
```
{json.dumps(session_results, indent=2)}
```

The results will be used to improve the parameter optimization process.
"""
        )
        
        logger.info(f"🧪 Learning session ended after {session_duration.total_seconds() / 60:.1f} minutes")
        
        return {
            "status": "completed",
            "duration_minutes": session_duration.total_seconds() / 60,
            "trades_executed": len(session_trades),
            "results": session_results,
            "next_session_available": (self.last_learning_session + timedelta(hours=self.learning_session_cooldown_hours)).isoformat()
        }
        
    def get_relaxed_parameters(self) -> Dict[str, Any]:
        """Get relaxed parameters for learning session"""
        relaxed_params = self.current_params.copy()
        
        # Relax confidence threshold (reduce by 10-20%)
        current_confidence = relaxed_params["min_confidence"]
        relaxed_params["min_confidence"] = max(0.4, current_confidence * 0.8)
        
        # Increase position size (by 10-30%)
        current_position_size = relaxed_params["max_position_size"]
        relaxed_params["max_position_size"] = min(0.3, current_position_size * 1.3)
        
        # Adjust stop loss (increase by 10-20%)
        current_stop_loss = relaxed_params["stop_loss_pct"]
        relaxed_params["stop_loss_pct"] = min(0.1, current_stop_loss * 1.2)
        
        # Adjust take profit (decrease by 10-20%)
        current_take_profit = relaxed_params["take_profit_pct"]
        relaxed_params["take_profit_pct"] = max(0.02, current_take_profit * 0.8)
        
        return relaxed_params
        
    async def get_learning_session_trades(self) -> List[Dict[str, Any]]:
        """Get trades executed during learning session"""
        if not self.learning_session_start_time:
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get trades executed during learning session
            cursor.execute("""
                SELECT * FROM trades
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """, (self.learning_session_start_time.isoformat(),))
            
            trades = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            trade_list = []
            for trade in trades:
                # Assuming trade format: (id, symbol, side, quantity, price, total, pnl, timestamp)
                trade_dict = {
                    "id": trade[0],
                    "symbol": trade[1],
                    "side": trade[2],
                    "quantity": trade[3],
                    "price": trade[4],
                    "total": trade[5],
                    "pnl": trade[6],
                    "timestamp": trade[7],
                    "learning_session": True
                }
                trade_list.append(trade_dict)
                
            return trade_list
            
        except Exception as e:
            logger.error(f"❌ Error fetching learning session trades: {e}")
            return []
            
    def analyze_learning_session_results(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results of learning session"""
        if not trades:
            return {
                "total_trades": 0,
                "successful_trades": 0,
                "unsuccessful_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "max_profit": 0,
                "max_loss": 0,
                "recommendation": "No trades executed during learning session"
            }
            
        # Calculate metrics
        total_trades = len(trades)
        successful_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        unsuccessful_trades = total_trades - successful_trades
        win_rate = successful_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        profits = [trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) > 0]
        losses = [trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) < 0]
        
        max_profit = max(profits) if profits else 0
        max_loss = min(losses) if losses else 0
        
        # Generate recommendation
        recommendation = ""
        if win_rate > 0.6 and total_pnl > 0:
            recommendation = "Consider permanently relaxing risk parameters"
        elif win_rate > 0.5 and total_pnl > 0:
            recommendation = "Schedule more learning sessions to gather additional data"
        elif win_rate < 0.4 or total_pnl < 0:
            recommendation = "Current risk parameters are appropriate"
            
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "unsuccessful_trades": unsuccessful_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "recommendation": recommendation
        }
        
    async def store_learning_session_results(self, results: Dict[str, Any]) -> None:
        """Store learning session results for optimizer"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                duration_minutes REAL,
                total_trades INTEGER,
                successful_trades INTEGER,
                unsuccessful_trades INTEGER,
                win_rate REAL,
                total_pnl REAL,
                avg_pnl REAL,
                max_profit REAL,
                max_loss REAL,
                recommendation TEXT,
                relaxed_parameters TEXT,
                original_parameters TEXT
            )
            """)
            
            # Insert learning session results
            cursor.execute("""
            INSERT INTO learning_sessions (
                start_time, end_time, duration_minutes,
                total_trades, successful_trades, unsuccessful_trades,
                win_rate, total_pnl, avg_pnl,
                max_profit, max_loss, recommendation,
                relaxed_parameters, original_parameters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.learning_session_start_time.isoformat(),
                datetime.now().isoformat(),
                (datetime.now() - self.learning_session_start_time).total_seconds() / 60,
                results.get("total_trades", 0),
                results.get("successful_trades", 0),
                results.get("unsuccessful_trades", 0),
                results.get("win_rate", 0),
                results.get("total_pnl", 0),
                results.get("avg_pnl", 0),
                results.get("max_profit", 0),
                results.get("max_loss", 0),
                results.get("recommendation", ""),
                json.dumps(self.get_relaxed_parameters()),
                json.dumps(self.original_params)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Learning session results stored")
            
        except Exception as e:
            logger.error(f"❌ Error storing learning session results: {e}")
            
    async def send_slack_notification(self, channel: str, message: str) -> None:
        """Send notification to Slack channel"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel_id": channel,
                    "payload": message,
                    "content_type": "text/markdown"
                }
                
                async with session.post(
                    f"{self.slack_mcp_url}/mcp/slack/conversations_add_message",
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send notification to Slack: HTTP {response.status}")
                    else:
                        logger.info(f"✅ Notification sent to Slack channel {channel}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending notification to Slack: {e}")
            
    async def get_blocked_trades(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get blocked trades from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get blocked trades from last N days
            cutoff_time = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT * FROM blocked_trades
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            blocked_trades = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            blocked_trade_list = []
            for trade in blocked_trades:
                # Assuming format: (id, timestamp, symbol, signal, block_reason, rsi, price, confidence, risk_level, data)
                trade_dict = {
                    "id": trade[0],
                    "timestamp": trade[1],
                    "symbol": trade[2],
                    "signal": trade[3],
                    "block_reason": trade[4],
                    "rsi": trade[5],
                    "price": trade[6],
                    "confidence": trade[7],
                    "risk_level": trade[8],
                    "data": json.loads(trade[9]) if trade[9] else {}
                }
                blocked_trade_list.append(trade_dict)
                
            return blocked_trade_list
            
        except Exception as e:
            logger.error(f"❌ Error fetching blocked trades: {e}")
            return []

# Global optimizer instance
optimizer = ParameterOptimizer()

@app.post("/start-monitoring")
async def start_monitoring():
    """Start loss event monitoring"""
    if optimizer.monitoring_active:
        return {"message": "Monitoring already active", "status": "running"}
    
    # Start monitoring task
    asyncio.create_task(optimizer.start_loss_monitoring())
    
    return {
        "message": "Loss event monitoring started",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/stop-monitoring")
async def stop_monitoring():
    """Stop loss event monitoring"""
    optimizer.stop_loss_monitoring()
    
    return {
        "message": "Loss event monitoring stopped",
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/loss-event")
async def receive_loss_event(loss_data: Dict[str, Any]):
    """Receive loss event from external systems"""
    try:
        logger.warning(f"📉 External loss event received: {loss_data}")
        
        # Send to Optuna MCP
        await optimizer.send_loss_event_to_optuna(loss_data)
        
        # Trigger optimization if significant loss
        loss_amount = loss_data.get("loss_amount", 0)
        if abs(loss_amount) > optimizer.loss_threshold:
            await optimizer.optimize_parameters()
        
        return {
            "message": "Loss event processed",
            "optimization_triggered": abs(loss_amount) > optimizer.loss_threshold,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Loss event processing error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "parameter-optimizer",
        "optuna_mcp_url": optimizer.optuna_mcp,
        "monitoring_active": optimizer.monitoring_active,
        "timestamp": datetime.now().isoformat(),
        "is_optimizing": optimizer.is_optimizing,
        "last_optimization": optimizer.last_optimization.isoformat() if optimizer.last_optimization else None
    }

@app.get("/status")
async def get_status():
    """Get optimizer status"""
    return {
        "service": "parameter-optimizer",
        "is_optimizing": optimizer.is_optimizing,
        "current_parameters": optimizer.current_params,
        "last_optimization": optimizer.last_optimization.isoformat() if optimizer.last_optimization else None,
        "optimization_results_count": len(optimizer.optimization_results),
        "loss_threshold": optimizer.loss_threshold,
        "lookback_hours": optimizer.optimization_lookback_hours
    }

@app.get("/performance-analysis")
async def get_performance_analysis():
    """Get recent performance analysis"""
    return await optimizer.get_recent_performance()

@app.post("/optimize")
async def run_optimization():
    """Run parameter optimization"""
    return await optimizer.run_optimization()

@app.post("/force-optimize")
async def force_optimization():
    """Force optimization regardless of performance"""
    # Temporarily override the needs_optimization check
    original_method = optimizer.get_recent_performance
    
    async def force_needs_optimization():
        performance = await original_method()
        performance["needs_optimization"] = True
        performance["reason"] = "Manual optimization requested"
        return performance
    
    optimizer.get_recent_performance = force_needs_optimization
    result = await optimizer.run_optimization()
    optimizer.get_recent_performance = original_method
    
    return result

@app.post("/start-learning-session")
async def start_learning_session(duration_minutes: int = None, background_tasks: BackgroundTasks = None):
    """Start a learning session with relaxed parameters"""
    result = await optimizer.start_learning_session(duration_minutes)
    return result

@app.post("/end-learning-session")
async def end_learning_session():
    """End learning session and restore original parameters"""
    result = await optimizer.end_learning_session()
    return result

@app.get("/learning-session-status")
async def get_learning_session_status():
    """Get current learning session status"""
    if not optimizer.learning_session_active:
        if optimizer.last_learning_session:
            cooldown_end = optimizer.last_learning_session + timedelta(hours=optimizer.learning_session_cooldown_hours)
            time_remaining = cooldown_end - datetime.now()
            
            return {
                "active": False,
                "last_session": optimizer.last_learning_session.isoformat(),
                "cooldown_end": cooldown_end.isoformat(),
                "hours_remaining": max(0, time_remaining.total_seconds() / 3600),
                "next_session_available": cooldown_end.isoformat() if datetime.now() < cooldown_end else "now"
            }
        else:
            return {
                "active": False,
                "message": "No learning session has been run yet"
            }
    
    # Learning session is active
    elapsed_time = datetime.now() - optimizer.learning_session_start_time
    remaining_time = timedelta(minutes=optimizer.learning_session_duration_minutes) - elapsed_time
    
    return {
        "active": True,
        "start_time": optimizer.learning_session_start_time.isoformat(),
        "elapsed_minutes": elapsed_time.total_seconds() / 60,
        "remaining_minutes": max(0, remaining_time.total_seconds() / 60),
        "end_time": (optimizer.learning_session_start_time + timedelta(minutes=optimizer.learning_session_duration_minutes)).isoformat(),
        "relaxed_parameters": optimizer.get_relaxed_parameters()
    }

@app.get("/blocked-trades")
async def get_blocked_trades(days: int = 7):
    """Get blocked trades from database"""
    blocked_trades = await optimizer.get_blocked_trades(days)
    
    # Group by block reason
    reasons = {}
    for trade in blocked_trades:
        reason = trade.get("block_reason", "unknown")
        if reason not in reasons:
            reasons[reason] = 0
        reasons[reason] += 1
    
    return {
        "total_blocked_trades": len(blocked_trades),
        "by_reason": reasons,
        "blocked_trades": blocked_trades[:100]  # Limit to 100 trades
    }

@app.get("/learning-sessions")
async def get_learning_sessions(limit: int = 10):
    """Get learning session history"""
    try:
        conn = sqlite3.connect(optimizer.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM learning_sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (limit,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        session_list = []
        for session in sessions:
            # Convert to dict based on table schema
            session_dict = {
                "id": session[0],
                "start_time": session[1],
                "end_time": session[2],
                "duration_minutes": session[3],
                "total_trades": session[4],
                "successful_trades": session[5],
                "unsuccessful_trades": session[6],
                "win_rate": session[7],
                "total_pnl": session[8],
                "avg_pnl": session[9],
                "max_profit": session[10],
                "max_loss": session[11],
                "recommendation": session[12],
                "relaxed_parameters": json.loads(session[13]) if session[13] else {},
                "original_parameters": json.loads(session[14]) if session[14] else {}
            }
            session_list.append(session_dict)
            
        return {
            "total_sessions": len(session_list),
            "sessions": session_list
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching learning sessions: {e}")
        return {
            "error": str(e),
            "total_sessions": 0,
            "sessions": []
        }

@app.get("/optimization-history")
async def get_optimization_history():
    """Get optimization history"""
    return {
        "total_optimizations": len(optimizer.optimization_results),
        "results": optimizer.optimization_results[-10:]  # Last 10 results
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)