#!/usr/bin/env python3
"""
Notification Service - Slack Notifications
Handles sending notifications to Slack channels
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging
import yaml
from datetime import datetime
from typing import Dict, Optional
import os
import json
import uvicorn
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Notification Service", version="2.0.0")

class SlackMessage(BaseModel):
    channel: str
    message: str

class NotificationManager:
    def __init__(self):
        self.config_path = os.getenv("CONFIG_PATH", "config/production_config.yaml")
        self.templates_path = os.getenv("TEMPLATES_PATH", "config/message_templates.yaml")
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = True
        self.channels = {}
        self.templates = {}
        self.load_config()
        logger.info("📢 Notification Manager initialized")

    def load_config(self):
        """Load configuration from YAML files"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            slack_config = self.config.get("slack", {})
            if not self.webhook_url:
                self.webhook_url = slack_config.get("webhook_url")
            self.enabled = slack_config.get("enabled", True)

            # Load message templates and channels
            with open(self.templates_path, 'r') as tf:
                templates_config = yaml.safe_load(tf)
                self.channels = {
                    "trading_alerts": os.getenv("SLACK_TRADING_ALERTS_CHANNEL", templates_config["slack_channels"]["trading_alerts"]),
                    "general": os.getenv("SLACK_GENERAL_CHANNEL", templates_config["slack_channels"]["general"])
                }
                self.templates = templates_config["templates"]

            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
            self.webhook_url = None
            self.enabled = False
            self.channels = {}
            self.templates = {}
    
    def send_slack_message(self, channel_key: str, message: str, channel_override: str = None) -> Dict:
        """Send message to Slack with Nova workspace support"""
        if not self.enabled or not self.webhook_url:
            logger.warning("📢 Slack notifications disabled or webhook not configured")
            return {"success": False, "error": "Slack not configured"}
        
        # Support for Nova workspace channel override
        if channel_override:
            channel = channel_override
        else:
            channel = self.channels.get(channel_key, channel_key)
        
        # Check if this is a Nova workspace channel ID
        nova_channel = os.getenv("SLACK_NOVA_TARGET_CHANNEL")
        if channel == "nova" or channel == nova_channel:
            channel = nova_channel  # Use the specific Nova channel ID
            
        try:
            payload = {
                "text": message,
                "username": "AI Trading Bot",
                "icon_emoji": ":robot_face:",
                "channel": channel if channel.startswith('#') or channel.startswith('C') else f"#{channel}"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            # Log with Nova workspace context
            workspace_info = ""
            if channel == nova_channel:
                workspace_info = f" (Nova workspace: {os.getenv('SLACK_NOVA_WORKSPACE', 'nova-mir4286.slack.com')})"
            
            logger.info(f"✅ Slack message sent to {channel}{workspace_info}")
            return {
                "success": True,
                "channel": channel,
                "workspace": os.getenv('SLACK_NOVA_WORKSPACE') if channel == nova_channel else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def send_trade_alert(self, trade_data: Dict) -> Dict:
        """Send trading alert to Slack"""
        if not trade_data.get("success"):
            return {"success": False, "error": "Invalid trade data"}
        
        side = trade_data.get("side", "")
        price = trade_data.get("price", 0)
        quantity = trade_data.get("quantity", 0)
        total = trade_data.get("total", 0)
        emoji = "🟢" if side == "BUY" else "🔴"
        time_str = datetime.now().strftime('%H:%M:%S')

        template = self.templates.get("trade_executed", "")
        message = string.Template(template).safe_substitute(
            emoji=emoji,
            side=side,
            price=price,
            quantity=quantity,
            total=total,
            time=time_str
        )

        return self.send_slack_message("trading_alerts", message)

    def send_backtest_report(self, backtest_results: Dict, strategy_name: str = "Unknown") -> Dict:
        """Send comprehensive backtest results to Slack with audit trail"""
        if not self.enabled:
            return {"success": False, "error": "Notifications disabled"}
        
        try:
            analysis = backtest_results.get("analysis", {})
            metadata = backtest_results.get("metadata", {})
            trades = backtest_results.get("trades", [])
            
            # Calculate additional metrics
            total_return = analysis.get('total_return', 0)
            win_rate = analysis.get('win_rate', 0)
            max_drawdown = analysis.get('max_drawdown', 0)
            sharpe_ratio = analysis.get('sharpe_ratio', 0)
            total_trades = len(trades)
            winning_trades = analysis.get('winning_trades', 0)
            losing_trades = analysis.get('losing_trades', 0)
            profit_factor = analysis.get('profit_factor', 0)
            
            # Determine performance level for emoji
            if total_return > 0.2:  # 20%+ return
                performance_emoji = "🚀"
                performance_level = "Excellent"
            elif total_return > 0.1:  # 10%+ return
                performance_emoji = "📈"
                performance_level = "Good"
            elif total_return > 0.05:  # 5%+ return
                performance_emoji = "✅"
                performance_level = "Acceptable"
            elif total_return > 0:  # Positive return
                performance_emoji = "⚠️"
                performance_level = "Marginal"
            else:  # Negative return
                performance_emoji = "❌"
                performance_level = "Poor"
            
            # Create comprehensive report
            report_header = f"*{performance_emoji} Backtest Report - {strategy_name}*\n"
            report_header += f"*Performance Level: {performance_level}*\n\n"
            
            # Core metrics
            core_metrics = (
                f"*📊 Core Performance Metrics:*\n"
                f"• Total Return: {total_return:.2%}\n"
                f"• Win Rate: {win_rate:.2%}\n"
                f"• Max Drawdown: {max_drawdown:.2%}\n"
                f"• Sharpe Ratio: {sharpe_ratio:.2f}\n"
                f"• Profit Factor: {profit_factor:.2f}\n\n"
            )
            
            # Trading statistics
            trade_stats = (
                f"*📈 Trading Statistics:*\n"
                f"• Total Trades: {total_trades}\n"
                f"• Winning Trades: {winning_trades}\n"
                f"• Losing Trades: {losing_trades}\n"
                f"• Average Win: {analysis.get('avg_win', 0):.2%}\n"
                f"• Average Loss: {analysis.get('avg_loss', 0):.2%}\n\n"
            )
            
            # Risk metrics
            risk_metrics = (
                f"*⚠️ Risk Analysis:*\n"
                f"• Value at Risk (95%): {analysis.get('var_95', 0):.2%}\n"
                f"• Maximum Consecutive Losses: {analysis.get('max_consecutive_losses', 0)}\n"
                f"• Volatility: {analysis.get('volatility', 0):.2%}\n"
                f"• Beta: {analysis.get('beta', 0):.2f}\n\n"
            )
            
            # Strategy parameters
            params = metadata.get('strategy_parameters', {})
            strategy_info = f"*🔧 Strategy Configuration:*\n"
            if params:
                for key, value in params.items():
                    strategy_info += f"• {key.replace('_', ' ').title()}: {value}\n"
            strategy_info += "\n"
            
            # Audit trail information
            audit_info = (
                f"*📋 Audit Information:*\n"
                f"• Backtest ID: {metadata.get('backtest_id', 'N/A')}\n"
                f"• Start Date: {metadata.get('start_date', 'N/A')}\n"
                f"• End Date: {metadata.get('end_date', 'N/A')}\n"
                f"• Initial Capital: ${metadata.get('initial_capital', 0):,.2f}\n"
                f"• Final Value: ${metadata.get('final_value', 0):,.2f}\n"
                f"• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            )
            
            # Validation status
            validation_status = self._get_validation_status(analysis)
            validation_info = f"*✅ Validation Status:* {validation_status}\n\n"
            
            # Performance thresholds check
            threshold_check = self._check_performance_thresholds(analysis)
            threshold_info = f"*🎯 Threshold Analysis:*\n{threshold_check}\n"
            
            # Combine all sections
            full_message = (
                report_header + core_metrics + trade_stats + 
                risk_metrics + strategy_info + audit_info + 
                validation_info + threshold_info
            )
            
            # Send to appropriate channel
            channel = "backtest_reports" if "backtest_reports" in self.channels else "trading_alerts"
            result = self.send_slack_message(channel, full_message)
            
            # Log audit trail
            self._log_backtest_audit(backtest_results, strategy_name, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send backtest report: {str(e)}")
            return {"success": False, "error": str(e)}

@app.post("/slack_command")
async def handle_slack_command(request: dict):
    """Handle Slack slash commands for configuration updates"""
    try:
        command = request.get("command", "")
        text = request.get("text", "")
        user_id = request.get("user_id", "")
        channel_id = request.get("channel_id", "")
        
        # Parse the command
        if command == "/trading-config":
            return await handle_config_command(text, user_id, channel_id)
        elif command == "/trading-status":
            return await handle_status_command(user_id, channel_id)
        elif command == "/trading-stop":
            return await handle_stop_command(user_id, channel_id)
        elif command == "/trading-start":
            return await handle_start_command(user_id, channel_id)
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}"
            }
            
    except Exception as e:
        logger.error(f"❌ Error handling Slack command: {e}")
        return {
            "response_type": "ephemeral", 
            "text": f"Error processing command: {str(e)}"
        }

async def handle_config_command(text: str, user_id: str, channel_id: str) -> dict:
    """Handle configuration update commands"""
    try:
        # Parse config update command
        # Format: /trading-config set <param> <value>
        # Example: /trading-config set max_position_size 0.15
        
        parts = text.strip().split()
        if len(parts) < 3 or parts[0] != "set":
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/trading-config set <parameter> <value>`\nExample: `/trading-config set max_position_size 0.15`"
            }
        
        param_name = parts[1]
        param_value = parts[2]
        
        # Validate parameter name and value
        valid_params = {
            "max_position_size": {"type": "float", "min": 0.01, "max": 1.0},
            "stop_loss_percentage": {"type": "float", "min": 0.001, "max": 0.5}, 
            "take_profit_percentage": {"type": "float", "min": 0.001, "max": 2.0},
            "trading_mode": {"type": "string", "values": ["paper", "live"]},
            "max_daily_trades": {"type": "int", "min": 1, "max": 1000},
            "risk_threshold": {"type": "float", "min": 0.01, "max": 1.0}
        }
        
        if param_name not in valid_params:
            return {
                "response_type": "ephemeral",
                "text": f"Invalid parameter: {param_name}\nValid parameters: {', '.join(valid_params.keys())}"
            }
        
        # Validate and convert value
        param_config = valid_params[param_name]
        try:
            if param_config["type"] == "float":
                value = float(param_value)
                if "min" in param_config and value < param_config["min"]:
                    raise ValueError(f"Value must be >= {param_config['min']}")
                if "max" in param_config and value > param_config["max"]:
                    raise ValueError(f"Value must be <= {param_config['max']}")
            elif param_config["type"] == "int":
                value = int(param_value)
                if "min" in param_config and value < param_config["min"]:
                    raise ValueError(f"Value must be >= {param_config['min']}")
                if "max" in param_config and value > param_config["max"]:
                    raise ValueError(f"Value must be <= {param_config['max']}")
            elif param_config["type"] == "string":
                value = param_value
                if "values" in param_config and value not in param_config["values"]:
                    raise ValueError(f"Value must be one of: {', '.join(param_config['values'])}")
        except ValueError as e:
            return {
                "response_type": "ephemeral",
                "text": f"Invalid value for {param_name}: {str(e)}"
            }
        
        # Send config update to orchestrator
        config_update_request = {
            "parameter": param_name,
            "value": value,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Make request to orchestrator to update config
        try:
            import requests
            response = requests.post(
                "http://localhost:8000/update_config",
                json=config_update_request,
                timeout=10
            )
            
            if response.status_code == 200:
                # Log the config change
                logger.info(f"CONFIG_UPDATE: {user_id} updated {param_name} to {value}")
                
                # Send confirmation to Slack
                confirmation_message = (
                    f"✅ Configuration updated successfully!\n"
                    f"Parameter: `{param_name}`\n" 
                    f"New Value: `{value}`\n"
                    f"Updated by: <@{user_id}>\n"
                    f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                
                # Send to config-updates channel if it exists
                if "config_updates" in notification_manager.channels:
                    notification_manager.send_slack_message("config_updates", confirmation_message)
                
                return {
                    "response_type": "in_channel",
                    "text": confirmation_message
                }
            else:
                error_msg = f"Failed to update configuration: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "response_type": "ephemeral",
                    "text": error_msg
                }
                
        except requests.RequestException as e:
            error_msg = f"Failed to communicate with orchestrator: {str(e)}"
            logger.error(error_msg)
            return {
                "response_type": "ephemeral", 
                "text": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error handling config command: {str(e)}")
        return {
            "response_type": "ephemeral",
            "text": f"Error processing config update: {str(e)}"
        }

async def handle_status_command(user_id: str, channel_id: str) -> dict:
    """Handle trading status command"""
    try:
        # Get status from orchestrator
        import requests
        response = requests.get("http://localhost:8000/system-status", timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            
            # Format status for Slack
            message = "📊 *Trading System Status*\n"
            for service, status in status_data.items():
                emoji = "✅" if status.get("status") == "healthy" else "❌"
                message += f"{emoji} {service}: {status.get('status', 'unknown')}\n"
            
            return {
                "response_type": "ephemeral",
                "text": message
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Failed to get system status: HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"Error getting status: {str(e)}"
        }

async def handle_stop_command(user_id: str, channel_id: str) -> dict:
    """Handle trading stop command"""
    try:
        import requests
        response = requests.post("http://localhost:8000/stop-orchestration", timeout=10)
        
        if response.status_code == 200:
            message = f"🛑 Trading stopped by <@{user_id}>"
            
            # Log the stop command
            logger.info(f"TRADING_STOP: {user_id} stopped trading")
            
            # Send to alerts channel
            notification_manager.send_slack_message("trading_alerts", message)
            
            return {
                "response_type": "in_channel",
                "text": message
            }
        else:
            return {
                "response_type": "ephemeral", 
                "text": f"Failed to stop trading: HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"Error stopping trading: {str(e)}"
        }

async def handle_start_command(user_id: str, channel_id: str) -> dict:
    """Handle trading start command"""
    try:
        import requests
        response = requests.post("http://localhost:8000/start-orchestration", timeout=10)
        
        if response.status_code == 200:
            message = f"🚀 Trading started by <@{user_id}>"
            
            # Log the start command
            logger.info(f"TRADING_START: {user_id} started trading")
            
            # Send to alerts channel
            notification_manager.send_slack_message("trading_alerts", message)
            
            return {
                "response_type": "in_channel", 
                "text": message
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Failed to start trading: HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"Error starting trading: {str(e)}"
        }
    
    def _get_validation_status(self, analysis: Dict) -> str:
        """Determine validation status based on analysis results"""
        total_return = analysis.get('total_return', 0)
        max_drawdown = analysis.get('max_drawdown', 0)
        sharpe_ratio = analysis.get('sharpe_ratio', 0)
        win_rate = analysis.get('win_rate', 0)
        
        # Define validation criteria
        min_return = 0.05  # 5% minimum return
        max_allowed_drawdown = 0.25  # 25% maximum drawdown
        min_sharpe = 0.5  # Minimum Sharpe ratio
        min_win_rate = 0.4  # 40% minimum win rate
        
        if (total_return >= min_return and 
            max_drawdown <= max_allowed_drawdown and 
            sharpe_ratio >= min_sharpe and 
            win_rate >= min_win_rate):
            return "✅ PASSED - Strategy approved for promotion"
        else:
            return "❌ FAILED - Strategy requires optimization"
    
    def _check_performance_thresholds(self, analysis: Dict) -> str:
        """Check performance against defined thresholds"""
        checks = []
        
        # Return threshold
        total_return = analysis.get('total_return', 0)
        if total_return >= 0.05:
            checks.append("✅ Return Threshold: PASS (≥5%)")
        else:
            checks.append(f"❌ Return Threshold: FAIL ({total_return:.2%} < 5%)")
        
        # Drawdown threshold
        max_drawdown = analysis.get('max_drawdown', 0)
        if max_drawdown <= 0.25:
            checks.append("✅ Drawdown Threshold: PASS (≤25%)")
        else:
            checks.append(f"❌ Drawdown Threshold: FAIL ({max_drawdown:.2%} > 25%)")
        
        # Sharpe ratio threshold
        sharpe_ratio = analysis.get('sharpe_ratio', 0)
        if sharpe_ratio >= 0.5:
            checks.append("✅ Sharpe Ratio: PASS (≥0.5)")
        else:
            checks.append(f"❌ Sharpe Ratio: FAIL ({sharpe_ratio:.2f} < 0.5)")
        
        # Win rate threshold
        win_rate = analysis.get('win_rate', 0)
        if win_rate >= 0.4:
            checks.append("✅ Win Rate: PASS (≥40%)")
        else:
            checks.append(f"❌ Win Rate: FAIL ({win_rate:.2%} < 40%)")
        
        return "\n".join(checks)
    
    def _log_backtest_audit(self, results: Dict, strategy_name: str, notification_result: Dict):
        """Log backtest audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "backtest_report",
            "strategy_name": strategy_name,
            "backtest_id": results.get("metadata", {}).get("backtest_id"),
            "total_return": results.get("analysis", {}).get("total_return"),
            "max_drawdown": results.get("analysis", {}).get("max_drawdown"),
            "sharpe_ratio": results.get("analysis", {}).get("sharpe_ratio"),
            "win_rate": results.get("analysis", {}).get("win_rate"),
            "notification_sent": notification_result.get("success", False),
            "validation_status": self._get_validation_status(results.get("analysis", {}))
        }
        
        # Log to file and optionally to database
        logger.info(f"BACKTEST_AUDIT: {audit_entry}")
        
        # Write to audit log file
        try:
            os.makedirs("logs", exist_ok=True)
            audit_file = "logs/backtest_audit.jsonl"
            with open(audit_file, "a") as f:
                f.write(f"{json.dumps(audit_entry)}\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")

# Global notification manager instance
notification_manager = NotificationManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification",
        "slack_enabled": notification_manager.enabled,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/slack")
async def send_slack_notification(slack_message: SlackMessage):
    """Send a Slack notification"""
    try:
        result = notification_manager.send_slack_message(
            slack_message.channel,
            slack_message.message
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error sending Slack notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade_alert")
async def send_trade_alert(trade_data: dict):
    """Send a trade alert to Slack"""
    try:
        result = notification_manager.send_trade_alert(trade_data)
        return result
    except Exception as e:
        logger.error(f"❌ Error sending trade alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest_report")
async def send_backtest_report(request: dict):
    """Send backtest results report with audit logging"""
    try:
        backtest_results = request.get("results", {})
        strategy_name = request.get("strategy_name", "Unknown Strategy")
        
        if not backtest_results:
            raise HTTPException(status_code=400, detail="No backtest results provided")
        
        result = notification_manager.send_backtest_report(backtest_results, strategy_name)
        return result
    except Exception as e:
        logger.error(f"❌ Error sending backtest report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nova")
async def send_nova_notification(request: dict):
    """Send notification to Nova workspace"""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Send to Nova workspace channel
        nova_channel = os.getenv("SLACK_NOVA_TARGET_CHANNEL", "C097REMKVK3")
        result = notification_manager.send_slack_message("nova", message, channel_override=nova_channel)
        return result
    except Exception as e:
        logger.error(f"❌ Error sending Nova notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test")
async def send_test_notification():
    """Send a test notification"""
    try:
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        template = notification_manager.templates.get("test_notification", "")
        test_message = string.Template(template).safe_substitute(time=time_str)
        result = notification_manager.send_slack_message("trading_alerts", test_message)
        return result
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test_nova")
async def send_test_nova_notification():
    """Send a test notification to Nova workspace"""
    try:
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_message = f"🤖 Nova Workspace Test - AI Trading System Connected! ({time_str})"
        
        # Send to Nova workspace
        nova_channel = os.getenv("SLACK_NOVA_TARGET_CHANNEL", "C097REMKVK3")
        result = notification_manager.send_slack_message("nova", test_message, channel_override=nova_channel)
        return result
    except Exception as e:
        logger.error(f"❌ Error sending Nova test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
