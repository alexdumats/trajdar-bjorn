#!/usr/bin/env python3
"""
Parameter Update Handler - Slack-driven parameter updates via MCP
Handles parameter update commands from Slack and applies them to the system
Integrates with the Slack MCP server for secure parameter management
"""

import asyncio
import aiohttp
import logging
import json
import yaml
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParameterUpdateHandler:
    """Handles Slack-driven parameter updates via MCP"""
    
    def __init__(self):
        # Configuration paths
        self.config_path = Path("config/agent_parameters.yaml")
        self.backup_dir = Path("config/backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load current configuration
        self.load_config()
        
        # Slack MCP integration
        self.slack_integration_url = os.getenv("SLACK_INTEGRATION_URL", "http://localhost:8009")
        
        # Parameter update settings
        self.enable_slack_updates = self.config.get("parameter_updates", {}).get("enable_slack_updates", True)
        self.update_channels = self.config.get("parameter_updates", {}).get("update_channels", [])
        self.authorized_users = self.parse_authorized_users()
        self.require_confirmation = self.config.get("parameter_updates", {}).get("require_confirmation", True)
        self.backup_before_update = self.config.get("parameter_updates", {}).get("backup_before_update", True)
        
        # Updateable and protected parameters
        self.updateable_categories = self.config.get("parameter_updates", {}).get("updateable_categories", [])
        self.protected_parameters = self.config.get("parameter_updates", {}).get("protected_parameters", [])
        
        # Parameter validation rules
        self.validation_rules = {
            "scheduling.intervals": {
                "type": "int",
                "min": 30,
                "max": 3600,
                "description": "Interval in seconds (30-3600)"
            },
            "market_analyst.analysis.min_confidence": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "description": "Confidence threshold (0.0-1.0)"
            },
            "news_analyst.analysis.max_articles_per_analysis": {
                "type": "int",
                "min": 5,
                "max": 100,
                "description": "Number of articles (5-100)"
            },
            "risk_manager.risk_levels": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "description": "Risk threshold (0.0-1.0)"
            }
        }
        
        # Pending updates for confirmation workflow
        self.pending_updates = {}
        
        logger.info("🔧 Parameter Update Handler initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
    
    def save_config(self):
        """Save configuration to YAML file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info("✅ Configuration saved")
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            raise
    
    def parse_authorized_users(self) -> List[str]:
        """Parse authorized users from environment variable"""
        users_str = os.getenv("SLACK_AUTHORIZED_USERS", "")
        if not users_str:
            return []
        return [user.strip() for user in users_str.split(",") if user.strip()]
    
    def backup_config(self) -> str:
        """Create a backup of the current configuration"""
        if not self.backup_before_update:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"agent_parameters_backup_{timestamp}.yaml"
        
        try:
            shutil.copy2(self.config_path, backup_path)
            logger.info(f"📋 Configuration backed up to: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"❌ Failed to backup config: {e}")
            return ""
    
    def validate_parameter_path(self, parameter: str) -> bool:
        """Validate if parameter path is updateable"""
        # Check if parameter is protected
        for protected in self.protected_parameters:
            if parameter.startswith(protected):
                return False
        
        # Check if parameter is in updateable categories
        for category in self.updateable_categories:
            if parameter.startswith(category):
                return True
        
        return False
    
    def validate_parameter_value(self, parameter: str, value: str) -> tuple[bool, Any, str]:
        """Validate parameter value and convert to appropriate type"""
        try:
            # Find matching validation rule
            validation_rule = None
            for rule_pattern, rule in self.validation_rules.items():
                if parameter.startswith(rule_pattern):
                    validation_rule = rule
                    break
            
            if not validation_rule:
                # Default validation - try to infer type from current value
                current_value = self.get_parameter_value(parameter)
                if isinstance(current_value, bool):
                    converted_value = value.lower() in ['true', '1', 'yes', 'on']
                    return True, converted_value, ""
                elif isinstance(current_value, int):
                    converted_value = int(value)
                    return True, converted_value, ""
                elif isinstance(current_value, float):
                    converted_value = float(value)
                    return True, converted_value, ""
                else:
                    return True, value, ""
            
            # Apply validation rule
            param_type = validation_rule["type"]
            
            if param_type == "int":
                converted_value = int(value)
                if "min" in validation_rule and converted_value < validation_rule["min"]:
                    return False, None, f"Value must be >= {validation_rule['min']}"
                if "max" in validation_rule and converted_value > validation_rule["max"]:
                    return False, None, f"Value must be <= {validation_rule['max']}"
                return True, converted_value, ""
            
            elif param_type == "float":
                converted_value = float(value)
                if "min" in validation_rule and converted_value < validation_rule["min"]:
                    return False, None, f"Value must be >= {validation_rule['min']}"
                if "max" in validation_rule and converted_value > validation_rule["max"]:
                    return False, None, f"Value must be <= {validation_rule['max']}"
                return True, converted_value, ""
            
            elif param_type == "bool":
                converted_value = value.lower() in ['true', '1', 'yes', 'on']
                return True, converted_value, ""
            
            else:
                return True, value, ""
                
        except ValueError as e:
            return False, None, f"Invalid {validation_rule.get('type', 'value')}: {e}"
        except Exception as e:
            return False, None, f"Validation error: {e}"
    
    def get_parameter_value(self, parameter: str) -> Any:
        """Get parameter value from config"""
        keys = parameter.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise ValueError(f"Parameter {parameter} not found")
        
        return value
    
    def set_parameter_value(self, parameter: str, value: Any) -> Any:
        """Set parameter value in config"""
        keys = parameter.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Get old value
        old_value = config.get(keys[-1], None)
        
        # Set new value
        config[keys[-1]] = value
        
        return old_value
    
    async def notify_slack(self, channel: str, message: str, thread_ts: Optional[str] = None):
        """Send notification to Slack via integration service"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": channel,
                    "message": message,
                    "priority": "normal"
                }
                
                async with session.post(
                    f"{self.slack_integration_url}/send-message",
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.debug(f"📤 Slack notification sent to {channel}")
                    else:
                        logger.error(f"❌ Failed to send Slack notification: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending Slack notification: {e}")
    
    async def handle_parameter_command(self, channel: str, user: str, command: str, thread_ts: Optional[str] = None) -> str:
        """Handle parameter update commands from Slack"""
        if not self.enable_slack_updates:
            return "❌ Parameter updates are disabled"
        
        if user not in self.authorized_users:
            return "❌ You are not authorized to update parameters"
        
        try:
            # Parse command
            parts = command.strip().split()
            if len(parts) < 2:
                return await self.get_parameter_help()
            
            action = parts[1].lower()
            
            if action == "show":
                return await self.handle_show_parameter(parts[2:])
            elif action == "set":
                return await self.handle_set_parameter(parts[2:], user, channel, thread_ts)
            elif action == "reset":
                return await self.handle_reset_parameter(parts[2:], user, channel, thread_ts)
            elif action == "list":
                return await self.handle_list_parameters()
            elif action == "confirm":
                return await self.handle_confirm_update(parts[2:], user, channel, thread_ts)
            elif action == "cancel":
                return await self.handle_cancel_update(parts[2:], user)
            elif action == "help":
                return await self.get_parameter_help()
            else:
                return f"❌ Unknown action: {action}. Use `/param help` for available commands."
                
        except Exception as e:
            logger.error(f"❌ Error handling parameter command: {e}")
            return f"❌ Error processing command: {e}"
    
    async def get_parameter_help(self) -> str:
        """Get parameter command help"""
        return """🔧 **Parameter Update Commands**

**Available Commands:**
• `/param show <parameter>` - Show current parameter value
• `/param set <parameter> <value>` - Set parameter to new value
• `/param reset <parameter>` - Reset parameter to default value
• `/param list [category]` - List available parameters
• `/param confirm <update_id>` - Confirm pending update
• `/param cancel <update_id>` - Cancel pending update
• `/param help` - Show this help message

**Examples:**
• `/param show market_analyst.analysis.min_confidence`
• `/param set market_analyst.analysis.min_confidence 0.75`
• `/param reset market_analyst.analysis.min_confidence`
• `/param list market_analyst`

**Updateable Categories:**
• `scheduling.intervals` - Agent scheduling intervals
• `market_analyst.analysis` - Market analysis parameters
• `news_analyst.analysis` - News analysis parameters
• `risk_manager.risk_levels` - Risk management thresholds
• `trade_executor.execution` - Trade execution settings

**Note:** Some updates require confirmation for safety."""
    
    async def handle_show_parameter(self, params: List[str]) -> str:
        """Handle show parameter command"""
        if not params:
            return "❌ Please specify a parameter to show"
        
        parameter = params[0]
        
        try:
            value = self.get_parameter_value(parameter)
            return f"""📋 **Parameter Value**

**Parameter:** `{parameter}`
**Current Value:** `{value}`
**Type:** `{type(value).__name__}`"""
        except Exception as e:
            return f"❌ Error getting parameter: {e}"
    
    async def handle_set_parameter(self, params: List[str], user: str, channel: str, thread_ts: Optional[str] = None) -> str:
        """Handle set parameter command"""
        if len(params) < 2:
            return "❌ Please specify parameter and value"
        
        parameter = params[0]
        new_value_str = " ".join(params[1:])
        
        # Validate parameter path
        if not self.validate_parameter_path(parameter):
            return f"❌ Parameter `{parameter}` is not updateable or is protected"
        
        # Validate parameter value
        is_valid, new_value, error_msg = self.validate_parameter_value(parameter, new_value_str)
        if not is_valid:
            return f"❌ Invalid value for `{parameter}`: {error_msg}"
        
        try:
            old_value = self.get_parameter_value(parameter)
            
            if self.require_confirmation:
                # Create pending update
                update_id = f"{user}_{int(datetime.now().timestamp())}"
                self.pending_updates[update_id] = {
                    "parameter": parameter,
                    "old_value": old_value,
                    "new_value": new_value,
                    "user": user,
                    "channel": channel,
                    "thread_ts": thread_ts,
                    "timestamp": datetime.now().isoformat()
                }
                
                return f"""⚠️ **Parameter Update Confirmation Required**

**Parameter:** `{parameter}`
**Current Value:** `{old_value}`
**New Value:** `{new_value}`
**Update ID:** `{update_id}`

Use `/param confirm {update_id}` to apply this change or `/param cancel {update_id}` to cancel."""
            
            else:
                # Apply update immediately
                return await self.apply_parameter_update(parameter, old_value, new_value, user, channel, thread_ts)
                
        except Exception as e:
            return f"❌ Error setting parameter: {e}"
    
    async def handle_confirm_update(self, params: List[str], user: str, channel: str, thread_ts: Optional[str] = None) -> str:
        """Handle confirm update command"""
        if not params:
            return "❌ Please specify update ID to confirm"
        
        update_id = params[0]
        
        if update_id not in self.pending_updates:
            return f"❌ Update ID `{update_id}` not found or expired"
        
        update = self.pending_updates[update_id]
        
        # Verify user authorization
        if update["user"] != user:
            return "❌ You can only confirm your own updates"
        
        try:
            # Apply the update
            result = await self.apply_parameter_update(
                update["parameter"],
                update["old_value"],
                update["new_value"],
                user,
                channel,
                thread_ts
            )
            
            # Remove from pending updates
            del self.pending_updates[update_id]
            
            return result
            
        except Exception as e:
            return f"❌ Error confirming update: {e}"
    
    async def handle_cancel_update(self, params: List[str], user: str) -> str:
        """Handle cancel update command"""
        if not params:
            return "❌ Please specify update ID to cancel"
        
        update_id = params[0]
        
        if update_id not in self.pending_updates:
            return f"❌ Update ID `{update_id}` not found"
        
        update = self.pending_updates[update_id]
        
        # Verify user authorization
        if update["user"] != user:
            return "❌ You can only cancel your own updates"
        
        # Remove from pending updates
        del self.pending_updates[update_id]
        
        return f"✅ Update `{update_id}` cancelled successfully"
    
    async def apply_parameter_update(self, parameter: str, old_value: Any, new_value: Any, user: str, channel: str, thread_ts: Optional[str] = None) -> str:
        """Apply parameter update"""
        try:
            # Backup configuration
            backup_path = self.backup_config()
            
            # Update parameter
            self.set_parameter_value(parameter, new_value)
            
            # Save configuration
            self.save_config()
            
            # Reload configuration
            self.load_config()
            
            # Notify about the update
            await self.notify_parameter_update(parameter, old_value, new_value, user, channel)
            
            # Notify affected services to reload configuration
            await self.notify_services_config_reload(parameter)
            
            success_msg = f"""✅ **Parameter Updated Successfully**

**Parameter:** `{parameter}`
**Old Value:** `{old_value}`
**New Value:** `{new_value}`
**Updated by:** {user}
**Time:** {datetime.now().strftime('%H:%M:%S')}"""
            
            if backup_path:
                success_msg += f"\n**Backup:** `{backup_path}`"
            
            return success_msg
            
        except Exception as e:
            logger.error(f"❌ Error applying parameter update: {e}")
            return f"❌ Error applying update: {e}"
    
    async def notify_parameter_update(self, parameter: str, old_value: Any, new_value: Any, user: str, channel: str):
        """Notify about parameter update"""
        message = f"""🔧 **Parameter Updated**

📝 **Parameter**: `{parameter}`
🔄 **Change**: `{old_value}` → `{new_value}`
👤 **Updated by**: {user}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}"""
        
        # Send to orchestrator channel
        await self.notify_slack("#orchestrator", message)
        
        # Send to the channel where the command was issued (if different)
        if channel != "#orchestrator":
            await self.notify_slack(channel, message)
    
    async def notify_services_config_reload(self, parameter: str):
        """Notify affected services to reload configuration"""
        # Determine which services need to reload based on parameter
        services_to_notify = []
        
        if parameter.startswith("market_analyst"):
            services_to_notify.append("http://localhost:8007")
        elif parameter.startswith("news_analyst"):
            services_to_notify.append("http://localhost:8008")
        elif parameter.startswith("risk_manager"):
            services_to_notify.append("http://localhost:8002")
        elif parameter.startswith("trade_executor"):
            services_to_notify.append("http://localhost:8005")
        elif parameter.startswith("parameter_optimizer"):
            services_to_notify.append("http://localhost:8006")
        elif parameter.startswith("scheduling"):
            services_to_notify.append("http://localhost:8010")  # Enhanced scheduler
        
        # Notify services (if they have reload endpoints)
        for service_url in services_to_notify:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{service_url}/reload-config", timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"✅ Notified {service_url} to reload config")
                        else:
                            logger.warning(f"⚠️ Service {service_url} reload returned {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to notify {service_url}: {e}")
    
    async def handle_list_parameters(self, category: Optional[str] = None) -> str:
        """Handle list parameters command"""
        if category:
            # List parameters in specific category
            params = []
            for updateable_category in self.updateable_categories:
                if category in updateable_category:
                    # Get parameters from config
                    try:
                        keys = updateable_category.split('.')
                        value = self.config
                        for key in keys:
                            value = value[key]
                        
                        if isinstance(value, dict):
                            for param_key in value.keys():
                                full_param = f"{updateable_category}.{param_key}"
                                params.append(full_param)
                    except:
                        continue
            
            if params:
                return f"📋 **Parameters in category `{category}`:**\n\n" + "\n".join(f"• `{p}`" for p in params[:20])
            else:
                return f"❌ No parameters found in category `{category}`"
        else:
            # List all updateable categories
            return f"""📋 **Updateable Parameter Categories:**

{chr(10).join(f"• `{cat}`" for cat in self.updateable_categories)}

Use `/param list <category>` to see parameters in a specific category."""
    
    async def handle_reset_parameter(self, params: List[str], user: str, channel: str, thread_ts: Optional[str] = None) -> str:
        """Handle reset parameter command"""
        if not params:
            return "❌ Please specify a parameter to reset"
        
        parameter = params[0]
        
        # Validate parameter path
        if not self.validate_parameter_path(parameter):
            return f"❌ Parameter `{parameter}` is not updateable or is protected"
        
        try:
            # Get current value
            old_value = self.get_parameter_value(parameter)
            
            # For now, we'll need to implement default value lookup
            # This would typically come from a defaults configuration file
            default_value = "default"  # TODO: Implement proper default value lookup
            
            return f"⚠️ Reset functionality not fully implemented yet. Current value: `{old_value}`"
            
        except Exception as e:
            return f"❌ Error resetting parameter: {e}"

# Global parameter update handler instance
parameter_handler = ParameterUpdateHandler()

# Async function to handle Slack commands
async def handle_slack_parameter_command(channel: str, user: str, command: str, thread_ts: Optional[str] = None) -> str:
    """Handle parameter command from Slack"""
    return await parameter_handler.handle_parameter_command(channel, user, command, thread_ts)

if __name__ == "__main__":
    # Test the parameter handler
    import asyncio
    
    async def test():
        handler = ParameterUpdateHandler()
        
        # Test show command
        result = await handler.handle_parameter_command(
            "#test", "U123456", "/param show market_analyst.analysis.min_confidence"
        )
        print(result)
        
        # Test help command
        result = await handler.handle_parameter_command(
            "#test", "U123456", "/param help"
        )
        print(result)
    
    asyncio.run(test())