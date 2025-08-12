"""
Slack Webhook Logger - Simple integration using webhook URL
Works immediately without bot token setup
"""

import os
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SlackWebhookLogger:
    """Simple Slack logger using webhook URL"""
    
    def __init__(self, agent_id: str, webhook_url: Optional[str] = None):
        self.agent_id = agent_id
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.session = None
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def send_message(self, text: str, blocks: Optional[list] = None) -> bool:
        """Send message to Slack via webhook"""
        try:
            session = await self._get_session()
            
            payload = {
                "text": text,
                "username": f"{self.agent_id.title()} Agent",
                "icon_emoji": self._get_agent_emoji(),
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=10
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error sending to Slack webhook: {e}")
            return False
    
    def _get_agent_emoji(self) -> str:
        """Get emoji for agent"""
        emoji_map = {
            "orchestrator": ":robot_face:",
            "portfolio": ":moneybag:",
            "signal": ":chart_with_upwards_trend:",
            "data": ":bar_chart:",
            "notification": ":bell:",
            "trading_bot": ":money_with_wings:",
            "assistant": ":speech_balloon:",
            "chaos_agent": ":fire:",
        }
        return emoji_map.get(self.agent_id, ":gear:")
    
    async def log_activity(self, activity_type: str, details: Dict[str, Any], 
                          level: str = "info") -> bool:
        """Log activity with structured formatting"""
        
        # Create emoji mapping for different activity types
        activity_emoji = {
            "trade": ":money_with_wings:",
            "signal": ":chart_with_upwards_trend:", 
            "data": ":bar_chart:",
            "error": ":x:",
            "warning": ":warning:",
            "info": ":information_source:",
            "success": ":white_check_mark:",
            "start": ":rocket:",
            "stop": ":stop_button:",
            "heartbeat": ":heartbeat:"
        }
        
        emoji = activity_emoji.get(activity_type, ":gear:")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Build message
        text = f"{emoji} **{self.agent_id.upper()} - {activity_type.upper()}**"
        
        # Create rich blocks for better formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {self.agent_id.upper()} - {activity_type.upper()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {timestamp}"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": f"*Level:* {level.upper()}"
                    }
                ]
            }
        ]
        
        # Add details section
        if details:
            detail_lines = []
            for key, value in details.items():
                if isinstance(value, (int, float)):
                    if key in ["price", "total"] and value > 0:
                        detail_lines.append(f"• *{key.title()}:* ${value:,.2f}")
                    elif key in ["quantity"] and value > 0:
                        detail_lines.append(f"• *{key.title()}:* {value:.6f}")
                    else:
                        detail_lines.append(f"• *{key.title()}:* {value}")
                else:
                    detail_lines.append(f"• *{key.title()}:* {value}")
            
            if detail_lines:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(detail_lines)
                    }
                })
        
        return await self.send_message(text, blocks)
    
    async def log_trade(self, side: str, quantity: float, price: float, 
                       total: float, additional_details: Optional[Dict] = None):
        """Log trade execution"""
        trade_details = {
            "side": side,
            "quantity": quantity,
            "price": price,
            "total": total,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        if additional_details:
            trade_details.update(additional_details)
        
        return await self.log_activity("trade", trade_details, "info")
    
    async def log_signal(self, signal_type: str, confidence: float, 
                        reason: str, additional_details: Optional[Dict] = None):
        """Log trading signal"""
        signal_details = {
            "signal_type": signal_type,
            "confidence": f"{confidence:.1%}" if confidence else "N/A",
            "reason": reason,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        if additional_details:
            signal_details.update(additional_details)
        
        return await self.log_activity("signal", signal_details, "info")
    
    async def log_error(self, error_message: str, details: Optional[Dict] = None):
        """Log error"""
        error_details = {"error_message": error_message}
        if details:
            error_details.update(details)
        return await self.log_activity("error", error_details, "error")
    
    async def log_info(self, info_message: str, details: Optional[Dict] = None):
        """Log info"""
        info_details = {"message": info_message}
        if details:
            info_details.update(details)
        return await self.log_activity("info", info_details, "info")
    
    async def log_success(self, success_message: str, details: Optional[Dict] = None):
        """Log success"""
        success_details = {"message": success_message}
        if details:
            success_details.update(details)
        return await self.log_activity("success", success_details, "success")
    
    async def send_heartbeat(self, status: str = "alive", metrics: Optional[Dict] = None):
        """Send heartbeat"""
        heartbeat_details = {"status": status}
        if metrics:
            heartbeat_details.update(metrics)
        return await self.log_activity("heartbeat", heartbeat_details, "info")
    
    async def log_start(self, start_message: str, details: Optional[Dict] = None):
        """Log start of a process or operation"""
        start_details = {"message": start_message}
        if details:
            start_details.update(details)
        return await self.log_activity("start", start_details, "info")


class SlackWebhookLoggerSync:
    """Synchronous wrapper for SlackWebhookLogger"""
    
    def __init__(self, agent_id: str, webhook_url: Optional[str] = None):
        self.async_logger = SlackWebhookLogger(agent_id, webhook_url)
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop, create a task
                task = asyncio.create_task(coro)
                return None  # Can't wait for result in running loop
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(coro)
    
    def log_activity(self, activity_type: str, details: Dict[str, Any], level: str = "info"):
        """Log activity synchronously"""
        self._run_async(self.async_logger.log_activity(activity_type, details, level))
    
    def log_error(self, error_message: str, details: Optional[Dict] = None):
        """Log error synchronously"""
        self._run_async(self.async_logger.log_error(error_message, details))
    
    def log_info(self, info_message: str, details: Optional[Dict] = None):
        """Log info synchronously"""
        self._run_async(self.async_logger.log_info(info_message, details))
    
    def log_trade(self, side: str, quantity: float, price: float, total: float, 
                 additional_details: Optional[Dict] = None):
        """Log trade synchronously"""
        self._run_async(self.async_logger.log_trade(side, quantity, price, total, additional_details))
    def send_heartbeat(self, status: str = "alive", metrics: Optional[Dict] = None):
        """Send heartbeat synchronously"""
        self._run_async(self.async_logger.send_heartbeat(status, metrics))
    
    def log_start(self, start_message: str, details: Optional[Dict] = None):
        """Log start of a process or operation synchronously"""
        self._run_async(self.async_logger.log_start(start_message, details))



# Convenience functions
def create_webhook_logger(agent_id: str, webhook_url: Optional[str] = None) -> SlackWebhookLogger:
    """Create async Slack webhook logger"""
    return SlackWebhookLogger(agent_id, webhook_url)

def create_sync_webhook_logger(agent_id: str, webhook_url: Optional[str] = None) -> SlackWebhookLoggerSync:
    """Create sync Slack webhook logger"""
    return SlackWebhookLoggerSync(agent_id, webhook_url)