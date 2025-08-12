#!/usr/bin/env python3
"""
Test Nova Workspace Integration
Simple test to verify direct Slack integration with Nova workspace
"""

import requests
import json
import os
import sys
from datetime import datetime

def test_nova_integration():
    """Test Nova workspace integration via notification service"""
    
    # Configuration
    notification_service_url = "http://135.181.164.232:8004"  # Hetzner server
    nova_channel = "C097REMKVK3"
    
    print("🚀 Testing Nova Workspace Integration")
    print("=" * 50)
    print(f"Server: {notification_service_url}")
    print(f"Nova Channel: {nova_channel}")
    print(f"Workspace: nova-mir4286.slack.com")
    print()
    
    # Test 1: Health check
    print("1️⃣ Testing notification service health...")
    try:
        response = requests.get(f"{notification_service_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service healthy: {health_data.get('status')}")
            print(f"   Slack enabled: {health_data.get('slack_enabled')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Send test message to Nova workspace
    print("\n2️⃣ Sending test message to Nova workspace...")
    try:
        test_message = f"🤖 Nova Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        payload = {
            "message": test_message
        }
        
        response = requests.post(
            f"{notification_service_url}/test_nova",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test message sent successfully!")
            print(f"   Channel: {result.get('channel')}")
            print(f"   Workspace: {result.get('workspace', 'N/A')}")
            print(f"   Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ Test message failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test message error: {e}")
        return False
    
    # Test 3: Send trading alert simulation
    print("\n3️⃣ Sending trading alert simulation...")
    try:
        alert_message = {
            "message": "🚨 **Trading Alert Simulation**\n\n" +
                      "📊 **Signal**: BUY BTCUSDC\n" +
                      "💰 **Price**: $50,000\n" +
                      "📈 **Confidence**: 85%\n" +
                      "⚡ **Action**: Paper trade executed\n\n" +
                      f"🕐 **Time**: {datetime.now().strftime('%H:%M:%S UTC')}\n" +
                      "🤖 **Source**: AI Trading System"
        }
        
        response = requests.post(
            f"{notification_service_url}/nova",
            json=alert_message,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Trading alert sent successfully!")
            print(f"   Channel: {result.get('channel')}")
            print(f"   Success: {result.get('success')}")
        else:
            print(f"❌ Trading alert failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Trading alert error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Nova Workspace Integration Test Complete!")
    print("\n📋 Next Steps:")
    print("1. Check your Nova Slack workspace for the test messages")
    print("2. Verify messages appear in channel C097REMKVK3")
    print("3. Confirm trading alerts are properly formatted")
    print("\n🔗 Nova Workspace URL:")
    print("https://nova-mir4286.slack.com/archives/C097REMKVK3")
    
    return True

if __name__ == "__main__":
    success = test_nova_integration()
    sys.exit(0 if success else 1)