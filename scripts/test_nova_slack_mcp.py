#!/usr/bin/env python3
"""
Nova Workspace Slack MCP Integration Test
Tests Slack MCP server integration with nova-mir4286.slack.com
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class NovaSlackMCPTester:
    def __init__(self):
        self.slack_mcp_url = "http://localhost:3001"
        self.target_channel = "C097REMKVK3"  # From Nova workspace URL
        self.workspace = "nova-mir4286.slack.com"
        self.team_id = "T096HMD0FDH"
        
        # Load environment variables
        self.slack_token = os.getenv("SLACK_MCP_XOXP_TOKEN")
        if not self.slack_token:
            print("❌ SLACK_MCP_XOXP_TOKEN not found in environment")
            sys.exit(1)
    
    async def test_health_check(self) -> bool:
        """Test Slack MCP server health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.slack_mcp_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Slack MCP Health Check: {health_data}")
                        return True
                    else:
                        print(f"❌ Health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_channels_list(self) -> bool:
        """Test listing channels in Nova workspace"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.slack_mcp_url}/channels_list") as response:
                    if response.status == 200:
                        channels = await response.json()
                        print(f"✅ Found {len(channels)} channels in Nova workspace")
                        
                        # Look for our target channel
                        target_found = False
                        for channel in channels:
                            if channel.get('id') == self.target_channel:
                                target_found = True
                                print(f"✅ Target channel found: {channel.get('name', 'Unknown')} ({self.target_channel})")
                                break
                        
                        if not target_found:
                            print(f"⚠️ Target channel {self.target_channel} not found in channel list")
                        
                        return True
                    else:
                        print(f"❌ Channels list failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Channels list error: {e}")
            return False
    
    async def test_send_message(self, test_message: str = None) -> bool:
        """Test sending a message to Nova workspace"""
        if not test_message:
            test_message = f"🤖 Nova Slack MCP Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": self.target_channel,
                    "text": test_message,
                    "username": "AI Trading Bot",
                    "icon_emoji": ":robot_face:"
                }
                
                async with session.post(
                    f"{self.slack_mcp_url}/conversations_add_message",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Message sent successfully to Nova workspace")
                        print(f"   Channel: {self.target_channel}")
                        print(f"   Message: {test_message}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Message send failed: {response.status}")
                        print(f"   Error: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Message send error: {e}")
            return False
    
    async def test_channel_history(self) -> bool:
        """Test reading channel history from Nova workspace"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "channel": self.target_channel,
                    "limit": 5
                }
                
                async with session.get(
                    f"{self.slack_mcp_url}/conversations_history",
                    params=params
                ) as response:
                    if response.status == 200:
                        history = await response.json()
                        messages = history.get('messages', [])
                        print(f"✅ Retrieved {len(messages)} recent messages from Nova workspace")
                        
                        # Show recent messages (without content for privacy)
                        for i, msg in enumerate(messages[:3]):
                            timestamp = datetime.fromtimestamp(float(msg.get('ts', 0)))
                            user = msg.get('user', 'Unknown')
                            print(f"   Message {i+1}: User {user} at {timestamp}")
                        
                        return True
                    else:
                        print(f"❌ Channel history failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Channel history error: {e}")
            return False
    
    async def test_trading_alert_simulation(self) -> bool:
        """Test sending a trading alert to Nova workspace"""
        trading_alert = {
            "channel": self.target_channel,
            "text": "🚨 Trading Alert - Nova Workspace Test",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🚨 Trading Alert - Test*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Symbol:*\nBTCUSDC"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Signal:*\nBUY"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Confidence:*\n85%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Price:*\n$50,000"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📊 *Technical Analysis:*\n• RSI: 25 (Oversold)\n• MACD: Bullish crossover\n• Volume: Above average"
                    }
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.slack_mcp_url}/conversations_add_message",
                    json=trading_alert,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        print("✅ Trading alert simulation sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Trading alert failed: {response.status}")
                        print(f"   Error: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Trading alert error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all Nova workspace integration tests"""
        print("🚀 Starting Nova Workspace Slack MCP Integration Tests")
        print(f"   Workspace: {self.workspace}")
        print(f"   Team ID: {self.team_id}")
        print(f"   Target Channel: {self.target_channel}")
        print(f"   MCP Server: {self.slack_mcp_url}")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Health Check
        print("\n1️⃣ Testing Slack MCP Server Health...")
        results['health_check'] = await self.test_health_check()
        
        # Test 2: Channels List
        print("\n2️⃣ Testing Channel List Access...")
        results['channels_list'] = await self.test_channels_list()
        
        # Test 3: Channel History
        print("\n3️⃣ Testing Channel History Access...")
        results['channel_history'] = await self.test_channel_history()
        
        # Test 4: Send Simple Message
        print("\n4️⃣ Testing Message Sending...")
        results['send_message'] = await self.test_send_message()
        
        # Test 5: Trading Alert Simulation
        print("\n5️⃣ Testing Trading Alert Simulation...")
        results['trading_alert'] = await self.test_trading_alert_simulation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        passed = sum(results.values())
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Nova Slack MCP integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the configuration and try again.")
        
        return results

async def main():
    """Main test execution"""
    tester = NovaSlackMCPTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())