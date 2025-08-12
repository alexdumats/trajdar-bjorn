#!/usr/bin/env python3
"""
Profit Monitor Service - Intelligent Profit Tracking and Alerting System

Features:
- Real-time profit/loss tracking with customizable thresholds
- Multi-channel notifications (Slack, Email, SMS)
- Trend analysis with historical comparisons
- Predictive modeling for profit projections
- Color-coded severity indicators
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import centralized configuration manager
try:
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.config_manager import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "profit_monitor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Profit Monitor Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alert severity levels
class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

# Alert channel types
class AlertChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    ALL = "all"

# Threshold configuration model
class ThresholdConfig(BaseModel):
    profit_target_pct: float = Field(1.0, description="Target profit percentage (default: 1%)")
    warning_threshold_pct: float = Field(0.5, description="Warning threshold percentage (default: 0.5%)")
    critical_threshold_pct: float = Field(-1.0, description="Critical threshold percentage (default: -1%)")
    time_window: str = Field("24h", description="Time window for profit calculation (e.g., 1h, 24h, 7d)")
    
# Alert configuration model
class AlertConfig(BaseModel):
    enabled: bool = True
    channels: List[AlertChannel] = [AlertChannel.SLACK]
    min_severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_minutes: int = 30

# Profit monitor configuration model
class ProfitMonitorConfig(BaseModel):
    thresholds: ThresholdConfig
    alerts: AlertConfig
    trend_analysis_enabled: bool = True
    prediction_enabled: bool = True
    check_interval_seconds: int = 60

class ProfitMonitor:
    def __init__(self):
        self.config_path = os.getenv("CONFIG_PATH", "/app/config/production_config.yaml")
        self.db_path = os.getenv("DB_PATH", "/app/database/paper_trading.db")
        
        # Load centralized configuration
        self.config = get_config()
        
        # Default configuration
        self.monitor_config = ProfitMonitorConfig(
            thresholds=ThresholdConfig(
                profit_target_pct=float(os.getenv("PROFIT_TARGET_PCT", "1.0")),
                warning_threshold_pct=float(os.getenv("WARNING_THRESHOLD_PCT", "0.5")),
                critical_threshold_pct=float(os.getenv("CRITICAL_THRESHOLD_PCT", "-1.0")),
                time_window=os.getenv("PROFIT_TIME_WINDOW", "24h")
            ),
            alerts=AlertConfig(
                enabled=os.getenv("ALERTS_ENABLED", "true").lower() == "true",
                channels=[AlertChannel(c) for c in os.getenv("ALERT_CHANNELS", "slack").split(",")],
                min_severity=AlertSeverity(os.getenv("MIN_ALERT_SEVERITY", "warning")),
                cooldown_minutes=int(os.getenv("ALERT_COOLDOWN_MINUTES", "30"))
            ),
            trend_analysis_enabled=os.getenv("TREND_ANALYSIS_ENABLED", "true").lower() == "true",
            prediction_enabled=os.getenv("PREDICTION_ENABLED", "true").lower() == "true",
            check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
        )
        
        # Alert state tracking
        self.last_alert_time = {
            AlertSeverity.INFO: None,
            AlertSeverity.WARNING: None,
            AlertSeverity.CRITICAL: None
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Historical profit data
        self.profit_history = []
        
        # Notification clients
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "sender_email": os.getenv("SENDER_EMAIL"),
            "sender_password": os.getenv("SENDER_PASSWORD"),
            "recipient_emails": os.getenv("RECIPIENT_EMAILS", "").split(",")
        }
        self.sms_config = {
            "api_key": os.getenv("SMS_API_KEY"),
            "from_number": os.getenv("SMS_FROM_NUMBER"),
            "to_numbers": os.getenv("SMS_TO_NUMBERS", "").split(",")
        }
        
        logger.info("🔍 Profit Monitor initialized")
    
    async def start_monitoring(self):
        """Start profit monitoring loop"""
        if self.monitoring_active:
            logger.warning("Profit monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("🚀 Starting profit monitoring")
        
        while self.monitoring_active:
            try:
                # Check profit against thresholds
                profit_data = await self.calculate_current_profit()
                
                # Store in history
                self.profit_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "profit_pct": profit_data["profit_percentage"],
                    "profit_amount": profit_data["profit_amount"],
                    "total_value": profit_data["total_value"]
                })
                
                # Trim history to last 1000 entries
                if len(self.profit_history) > 1000:
                    self.profit_history = self.profit_history[-1000:]
                
                # Check thresholds and send alerts if needed
                await self.check_thresholds(profit_data)
                
                # Run trend analysis if enabled
                if self.monitor_config.trend_analysis_enabled and len(self.profit_history) > 10:
                    trend_data = self.analyze_profit_trend()
                    logger.info(f"📈 Trend analysis: {trend_data['trend']} ({trend_data['slope']:.4f})")
                
                # Run prediction if enabled
                if self.monitor_config.prediction_enabled and len(self.profit_history) > 24:
                    prediction = self.predict_future_profit()
                    logger.info(f"🔮 Profit prediction (24h): {prediction['prediction_24h']:.2f}%")
                
                # Wait for next check interval
                await asyncio.sleep(self.monitor_config.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Profit monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def stop_monitoring(self):
        """Stop profit monitoring loop"""
        self.monitoring_active = False
        logger.info("🛑 Profit monitoring stopped")
    
    async def calculate_current_profit(self) -> Dict[str, Any]:
        """Calculate current profit based on portfolio data"""
        try:
            # Parse time window
            time_window = self.monitor_config.thresholds.time_window
            hours = 24  # Default to 24 hours
            
            if time_window.endswith('h'):
                hours = int(time_window[:-1])
            elif time_window.endswith('d'):
                hours = int(time_window[:-1]) * 24
            elif time_window.endswith('w'):
                hours = int(time_window[:-1]) * 24 * 7
            
            # Calculate time threshold
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current portfolio value
            cursor.execute("SELECT total_value FROM paper_portfolio WHERE id = 1")
            current_value = cursor.fetchone()[0]
            
            # Get portfolio value at start of time window
            cursor.execute("""
                SELECT total_value FROM portfolio_snapshots 
                WHERE timestamp < ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (time_threshold.isoformat(),))
            
            result = cursor.fetchone()
            if result:
                start_value = result[0]
            else:
                # Fallback to starting balance if no snapshot found
                cursor.execute("SELECT starting_balance FROM paper_portfolio WHERE id = 1")
                start_value = cursor.fetchone()[0]
            
            # Calculate profit
            profit_amount = current_value - start_value
            profit_percentage = (profit_amount / start_value) * 100 if start_value > 0 else 0
            
            # Get recent trades
            cursor.execute("""
                SELECT * FROM paper_trades
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (time_threshold.isoformat(),))
            
            trades = cursor.fetchall()
            conn.close()
            
            # Calculate additional metrics
            win_trades = sum(1 for trade in trades if trade[6] > 0)  # Assuming pnl is at index 6
            total_trades = len(trades)
            win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            return {
                "profit_amount": profit_amount,
                "profit_percentage": profit_percentage,
                "total_value": current_value,
                "start_value": start_value,
                "time_window": time_window,
                "trades_count": total_trades,
                "win_rate": win_rate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating profit: {e}")
            return {
                "profit_amount": 0,
                "profit_percentage": 0,
                "total_value": 0,
                "start_value": 0,
                "time_window": self.monitor_config.thresholds.time_window,
                "trades_count": 0,
                "win_rate": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def check_thresholds(self, profit_data: Dict[str, Any]):
        """Check profit against thresholds and send alerts if needed"""
        profit_pct = profit_data["profit_percentage"]
        thresholds = self.monitor_config.thresholds
        
        # Determine severity based on thresholds
        severity = None
        if profit_pct <= thresholds.critical_threshold_pct:
            severity = AlertSeverity.CRITICAL
        elif profit_pct <= thresholds.warning_threshold_pct:
            severity = AlertSeverity.WARNING
        elif profit_pct >= thresholds.profit_target_pct:
            severity = AlertSeverity.INFO
        
        # Send alert if severity is determined and alerts are enabled
        if severity and self.monitor_config.alerts.enabled:
            # Check if severity meets minimum threshold
            if self._severity_level(severity) >= self._severity_level(self.monitor_config.alerts.min_severity):
                # Check cooldown
                last_alert = self.last_alert_time[severity]
                cooldown = timedelta(minutes=self.monitor_config.alerts.cooldown_minutes)
                
                if not last_alert or (datetime.now() - last_alert) > cooldown:
                    # Send alert
                    await self.send_alert(severity, profit_data)
                    self.last_alert_time[severity] = datetime.now()
    
    def _severity_level(self, severity: AlertSeverity) -> int:
        """Convert severity enum to numeric level for comparison"""
        levels = {
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.CRITICAL: 3
        }
        return levels.get(severity, 0)
    
    async def send_alert(self, severity: AlertSeverity, profit_data: Dict[str, Any]):
        """Send alert through configured channels"""
        # Prepare alert message
        message = self._format_alert_message(severity, profit_data)
        
        # Determine which channels to use
        channels = self.monitor_config.alerts.channels
        if AlertChannel.ALL in channels:
            channels = [AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SMS]
        
        # Send to each channel
        for channel in channels:
            if channel == AlertChannel.SLACK:
                await self._send_slack_alert(severity, message)
            elif channel == AlertChannel.EMAIL:
                await self._send_email_alert(severity, message)
            elif channel == AlertChannel.SMS:
                await self._send_sms_alert(severity, message)
        
        logger.info(f"🚨 Sent {severity} alert via {', '.join([c.value for c in channels])}")
    
    def _format_alert_message(self, severity: AlertSeverity, profit_data: Dict[str, Any]) -> str:
        """Format alert message based on severity and profit data"""
        profit_pct = profit_data["profit_percentage"]
        profit_amount = profit_data["profit_amount"]
        time_window = profit_data["time_window"]
        
        # Emoji based on severity
        emoji = "🔴" if severity == AlertSeverity.CRITICAL else "🟠" if severity == AlertSeverity.WARNING else "🟢"
        
        # Message title based on severity
        if severity == AlertSeverity.CRITICAL:
            title = "CRITICAL PROFIT ALERT"
        elif severity == AlertSeverity.WARNING:
            title = "Profit Warning"
        else:
            title = "Profit Target Reached"
        
        # Format message
        message = f"{emoji} *{title}*\n\n"
        message += f"• Profit: {profit_pct:.2f}% (${profit_amount:.2f})\n"
        message += f"• Time Window: {time_window}\n"
        message += f"• Current Value: ${profit_data['total_value']:.2f}\n"
        
        if profit_data.get("trades_count", 0) > 0:
            message += f"• Trades: {profit_data['trades_count']} (Win Rate: {profit_data['win_rate']:.1%})\n"
        
        # Add threshold information
        thresholds = self.monitor_config.thresholds
        message += f"\n*Thresholds*:\n"
        message += f"• Target: {thresholds.profit_target_pct:.2f}%\n"
        message += f"• Warning: {thresholds.warning_threshold_pct:.2f}%\n"
        message += f"• Critical: {thresholds.critical_threshold_pct:.2f}%\n"
        
        # Add trend information if available
        if self.monitor_config.trend_analysis_enabled and len(self.profit_history) > 10:
            trend_data = self.analyze_profit_trend()
            message += f"\n*Trend Analysis*: {trend_data['trend']} ({trend_data['slope']:.4f})\n"
        
        # Add prediction if available
        if self.monitor_config.prediction_enabled and len(self.profit_history) > 24:
            prediction = self.predict_future_profit()
            message += f"\n*Prediction (24h)*: {prediction['prediction_24h']:.2f}%\n"
        
        message += f"\n_Alert generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return message
    
    async def _send_slack_alert(self, severity: AlertSeverity, message: str):
        """Send alert to Slack"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Set color based on severity
        color = "#ff0000" if severity == AlertSeverity.CRITICAL else "#ffa500" if severity == AlertSeverity.WARNING else "#36a64f"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message,
                    "mrkdwn_in": ["text"]
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send Slack alert: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    async def _send_email_alert(self, severity: AlertSeverity, message: str):
        """Send alert via email"""
        if not self.email_config["sender_email"] or not self.email_config["sender_password"] or not self.email_config["recipient_emails"]:
            logger.warning("Email configuration incomplete")
            return
        
        # Convert markdown to plain text
        plain_message = message.replace('*', '').replace('_', '')
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = self.email_config["sender_email"]
        msg['To'] = ", ".join(self.email_config["recipient_emails"])
        
        # Set subject based on severity
        if severity == AlertSeverity.CRITICAL:
            msg['Subject'] = "🔴 CRITICAL PROFIT ALERT"
        elif severity == AlertSeverity.WARNING:
            msg['Subject'] = "🟠 Profit Warning"
        else:
            msg['Subject'] = "🟢 Profit Target Reached"
        
        # Attach message
        msg.attach(MIMEText(plain_message, 'plain'))
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["sender_email"], self.email_config["sender_password"])
            
            # Send email
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def _send_sms_alert(self, severity: AlertSeverity, message: str):
        """Send alert via SMS"""
        if not self.sms_config["api_key"] or not self.sms_config["from_number"] or not self.sms_config["to_numbers"]:
            logger.warning("SMS configuration incomplete")
            return
        
        # Convert markdown to plain text and truncate for SMS
        plain_message = message.replace('*', '').replace('_', '')
        truncated_message = plain_message[:160] + "..." if len(plain_message) > 160 else plain_message
        
        # This is a placeholder for an SMS API integration
        # In a real implementation, you would use a service like Twilio, Nexmo, etc.
        logger.info(f"SMS alert would be sent to {self.sms_config['to_numbers']}: {truncated_message}")
        
        # Example Twilio integration (commented out)
        """
        from twilio.rest import Client
        
        client = Client(self.sms_config["account_sid"], self.sms_config["api_key"])
        
        for to_number in self.sms_config["to_numbers"]:
            try:
                message = client.messages.create(
                    body=truncated_message,
                    from_=self.sms_config["from_number"],
                    to=to_number
                )
                logger.info(f"SMS sent to {to_number}, SID: {message.sid}")
            except Exception as e:
                logger.error(f"Error sending SMS to {to_number}: {e}")
        """
    
    def analyze_profit_trend(self) -> Dict[str, Any]:
        """Analyze profit trend from historical data"""
        if len(self.profit_history) < 10:
            return {"trend": "insufficient_data", "slope": 0.0}
        
        try:
            # Extract timestamps and profit percentages
            timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in self.profit_history]
            profits = [entry["profit_pct"] for entry in self.profit_history]
            
            # Convert timestamps to numeric values (seconds since epoch)
            x = np.array([(ts - timestamps[0]).total_seconds() for ts in timestamps]).reshape(-1, 1)
            y = np.array(profits)
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(x, y)
            
            # Get slope
            slope = model.coef_[0]
            
            # Determine trend
            if abs(slope) < 0.0001:
                trend = "stable"
            elif slope > 0:
                trend = "upward" if slope > 0.001 else "slightly_upward"
            else:
                trend = "downward" if slope < -0.001 else "slightly_downward"
            
            return {
                "trend": trend,
                "slope": float(slope),
                "r_squared": float(model.score(x, y)),
                "data_points": len(self.profit_history)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing profit trend: {e}")
            return {"trend": "error", "slope": 0.0, "error": str(e)}
    
    def predict_future_profit(self) -> Dict[str, Any]:
        """Predict future profit based on historical data"""
        if len(self.profit_history) < 24:
            return {"prediction_24h": 0.0, "confidence": 0.0}
        
        try:
            # Extract timestamps and profit percentages
            timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in self.profit_history]
            profits = [entry["profit_pct"] for entry in self.profit_history]
            
            # Convert timestamps to numeric values (hours since first entry)
            x = np.array([(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]).reshape(-1, 1)
            y = np.array(profits)
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(x, y)
            
            # Predict 24 hours ahead
            last_hour = x[-1][0]
            prediction_24h = model.predict(np.array([[last_hour + 24]]))[0]
            
            # Calculate confidence (simplified as R-squared)
            confidence = model.score(x, y)
            
            return {
                "prediction_24h": float(prediction_24h),
                "confidence": float(confidence),
                "model": "linear_regression",
                "data_points": len(self.profit_history)
            }
            
        except Exception as e:
            logger.error(f"Error predicting future profit: {e}")
            return {"prediction_24h": 0.0, "confidence": 0.0, "error": str(e)}
    
    async def update_configuration(self, new_config: ProfitMonitorConfig) -> bool:
        """Update profit monitor configuration"""
        try:
            self.monitor_config = new_config
            
            # Update environment variables
            os.environ["PROFIT_TARGET_PCT"] = str(new_config.thresholds.profit_target_pct)
            os.environ["WARNING_THRESHOLD_PCT"] = str(new_config.thresholds.warning_threshold_pct)
            os.environ["CRITICAL_THRESHOLD_PCT"] = str(new_config.thresholds.critical_threshold_pct)
            os.environ["PROFIT_TIME_WINDOW"] = new_config.thresholds.time_window
            os.environ["ALERTS_ENABLED"] = str(new_config.alerts.enabled).lower()
            os.environ["ALERT_CHANNELS"] = ",".join([c.value for c in new_config.alerts.channels])
            os.environ["MIN_ALERT_SEVERITY"] = new_config.alerts.min_severity.value
            os.environ["ALERT_COOLDOWN_MINUTES"] = str(new_config.alerts.cooldown_minutes)
            os.environ["TREND_ANALYSIS_ENABLED"] = str(new_config.trend_analysis_enabled).lower()
            os.environ["PREDICTION_ENABLED"] = str(new_config.prediction_enabled).lower()
            os.environ["CHECK_INTERVAL_SECONDS"] = str(new_config.check_interval_seconds)
            
            logger.info("✅ Profit monitor configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration update failed: {e}")
            return False

# Global profit monitor instance
profit_monitor = ProfitMonitor()

@app.post("/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start profit monitoring"""
    if profit_monitor.monitoring_active:
        return {"message": "Monitoring already active", "status": "running"}
    
    # Start monitoring in background
    background_tasks.add_task(profit_monitor.start_monitoring)
    
    return {
        "message": "Profit monitoring started",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "config": profit_monitor.monitor_config
    }

@app.post("/stop-monitoring")
async def stop_monitoring():
    """Stop profit monitoring"""
    profit_monitor.stop_monitoring()
    
    return {
        "message": "Profit monitoring stopped",
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/current-profit")
async def get_current_profit():
    """Get current profit data"""
    return await profit_monitor.calculate_current_profit()

@app.get("/profit-history")
async def get_profit_history(limit: int = Query(100, ge=1, le=1000)):
    """Get profit history"""
    history = profit_monitor.profit_history[-limit:] if limit < len(profit_monitor.profit_history) else profit_monitor.profit_history
    
    return {
        "history": history,
        "count": len(history),
        "total_records": len(profit_monitor.profit_history)
    }

@app.get("/trend-analysis")
async def get_trend_analysis():
    """Get profit trend analysis"""
    if not profit_monitor.monitor_config.trend_analysis_enabled:
        return {"status": "disabled", "message": "Trend analysis is disabled"}
    
    if len(profit_monitor.profit_history) < 10:
        return {"status": "insufficient_data", "message": "Need at least 10 data points for trend analysis"}
    
    return profit_monitor.analyze_profit_trend()

@app.get("/profit-prediction")
async def get_profit_prediction():
    """Get profit prediction"""
    if not profit_monitor.monitor_config.prediction_enabled:
        return {"status": "disabled", "message": "Prediction is disabled"}
    
    if len(profit_monitor.profit_history) < 24:
        return {"status": "insufficient_data", "message": "Need at least 24 data points for prediction"}
    
    return profit_monitor.predict_future_profit()

@app.get("/config")
async def get_config():
    """Get current profit monitor configuration"""
    return profit_monitor.monitor_config

@app.post("/config")
async def update_config(config: ProfitMonitorConfig):
    """Update profit monitor configuration"""
    success = await profit_monitor.update_configuration(config)
    
    if success:
        return {
            "status": "success",
            "message": "Configuration updated",
            "config": profit_monitor.monitor_config
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@app.post("/test-alert")
async def test_alert(severity: AlertSeverity = AlertSeverity.INFO, channel: AlertChannel = AlertChannel.SLACK):
    """Send test alert"""
    # Get current profit data
    profit_data = await profit_monitor.calculate_current_profit()
    
    # Override channels for test
    original_channels = profit_monitor.monitor_config.alerts.channels
    profit_monitor.monitor_config.alerts.channels = [channel]
    
    # Send alert
    await profit_monitor.send_alert(severity, profit_data)
    
    # Restore original channels
    profit_monitor.monitor_config.alerts.channels = original_channels
    
    return {
        "status": "success",
        "message": f"Test alert sent with severity {severity} via {channel}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "profit-monitor",
        "monitoring_active": profit_monitor.monitoring_active,
        "timestamp": datetime.now().isoformat(),
        "config": profit_monitor.monitor_config
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)