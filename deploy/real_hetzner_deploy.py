#!/usr/bin/env python3
"""
Real Hetzner Cloud Deployment Script
Creates actual Hetzner server and deploys the AI trading system
"""

import asyncio
import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional

class RealHetznerDeployment:
    def __init__(self):
        self.api_token = os.getenv('HETZNER_API_TOKEN')
        if not self.api_token:
            raise ValueError("HETZNER_API_TOKEN environment variable is required")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        self.server_config = {
            "name": "ai-trading-prod",
            "server_type": "cpx31",  # 4 vCPU, 8GB RAM, 160GB SSD (current generation)
            "location": "nbg1",      # Nuremberg
            "image": "ubuntu-22.04",
            "ssh_keys": [],  # Will be populated
            "labels": {
                "environment": "production",
                "project": "ai-trading-system"
            },
            "user_data": self._generate_cloud_init_config()
        }

    def _generate_cloud_init_config(self) -> str:
        """Generate cloud-init configuration for server setup"""
        return """#cloud-config
packages:
  - docker.io
  - docker-compose
  - python3
  - python3-pip
  - git
  - curl
  - wget
  - htop
  - ufw

runcmd:
  # Update system
  - apt-get update && apt-get upgrade -y
  
  # Install Docker Compose
  - curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  - chmod +x /usr/local/bin/docker-compose
  
  # Install Go for Slack MCP server
  - wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
  - tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
  - echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
  
  # Install Node.js
  - curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  - apt-get install -y nodejs
  
  # Create trading user
  - useradd -m -s /bin/bash trading
  - usermod -aG docker trading
  - usermod -aG sudo trading
  
  # Set up SSH key for trading user
  - mkdir -p /home/trading/.ssh
  - cp /root/.ssh/authorized_keys /home/trading/.ssh/authorized_keys
  - chown -R trading:trading /home/trading/.ssh
  - chmod 700 /home/trading/.ssh
  - chmod 600 /home/trading/.ssh/authorized_keys
  
  # Create application directory
  - mkdir -p /opt/ai-trading-system
  - chown trading:trading /opt/ai-trading-system
  
  # Configure firewall
  - ufw allow 22/tcp
  - ufw allow 8000/tcp
  - ufw allow 9000/tcp
  - ufw --force enable

users:
  - name: trading
    groups: [docker, sudo]
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']

final_message: |
  AI Trading System server is ready!
  - Docker and Docker Compose installed
  - Trading user created with sudo access
  - Firewall configured for ports 22, 8000, 9000
  - Ready for deployment
"""

    def get_ssh_keys(self) -> list:
        """Get available SSH keys from Hetzner"""
        try:
            response = requests.get(
                'https://api.hetzner.cloud/v1/ssh_keys',
                headers=self.headers
            )
            response.raise_for_status()
            keys = response.json().get('ssh_keys', [])
            return [key['id'] for key in keys]
        except Exception as e:
            print(f"⚠️ Warning: Could not fetch SSH keys: {e}")
            return []

    def create_server(self) -> Optional[Dict[str, Any]]:
        """Create Hetzner Cloud server"""
        try:
            print("🏗️ Creating Hetzner Cloud server...")
            
            # Get SSH keys
            ssh_keys = self.get_ssh_keys()
            self.server_config['ssh_keys'] = ssh_keys
            
            response = requests.post(
                'https://api.hetzner.cloud/v1/servers',
                headers=self.headers,
                json=self.server_config
            )
            
            if response.status_code == 201:
                server_data = response.json()
                server = server_data['server']
                action = server_data['action']
                
                print(f"✅ Server creation initiated!")
                print(f"   Server ID: {server['id']}")
                print(f"   Server Name: {server['name']}")
                print(f"   Action ID: {action['id']}")
                
                return server
            else:
                print(f"❌ Failed to create server: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating server: {e}")
            return None

    def wait_for_server_ready(self, server_id: int, max_wait: int = 300) -> Optional[str]:
        """Wait for server to be running and get IP"""
        print("⏳ Waiting for server to be ready...")
        
        for i in range(max_wait):
            try:
                response = requests.get(
                    f'https://api.hetzner.cloud/v1/servers/{server_id}',
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    server = response.json()['server']
                    status = server['status']
                    
                    print(f"   Status: {status} ({i+1}/{max_wait})")
                    
                    if status == 'running' and server['public_net']['ipv4']['ip']:
                        ip = server['public_net']['ipv4']['ip']
                        print(f"✅ Server is ready! IP: {ip}")
                        return ip
                
                time.sleep(2)
                
            except Exception as e:
                print(f"   Error checking server: {e}")
                time.sleep(5)
        
        print("❌ Server did not become ready within timeout")
        return None

    def generate_deployment_script(self, server_ip: str) -> str:
        """Generate deployment script for the server"""
        return f"""#!/bin/bash
set -e

echo "🚀 Starting AI Trading System deployment to {server_ip}"

# Variables
SERVER_IP="{server_ip}"
PROJECT_DIR="/opt/ai-trading-system"

# Function to run commands on remote server
run_remote() {{
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 trading@$SERVER_IP "$@"
}}

# Function to copy files to remote server
copy_to_remote() {{
    scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -r "$1" trading@$SERVER_IP:"$2"
}}

echo "🔄 Testing connection to server..."
if ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 trading@$SERVER_IP "echo 'Connection successful'"; then
    echo "❌ Cannot connect to server. Please check:"
    echo "   1. Server is running"
    echo "   2. SSH key is properly configured"
    echo "   3. Firewall allows SSH (port 22)"
    exit 1
fi

echo "📂 Preparing project directory..."
run_remote "sudo mkdir -p $PROJECT_DIR && sudo chown trading:trading $PROJECT_DIR"

echo "📦 Copying project files..."
copy_to_remote "." "$PROJECT_DIR/"

echo "🔑 Setting up environment variables..."
copy_to_remote ".env.production" "$PROJECT_DIR/.env.production"

echo "🐳 Building and starting Docker containers..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml pull || true"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml build"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml up -d"

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service health..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml ps"

echo "🌐 Testing system endpoints..."
if run_remote "curl -f http://localhost:8000/health"; then
    echo "✅ Orchestrator is healthy"
else
    echo "⚠️ Orchestrator not ready yet"
fi

if run_remote "curl -f http://localhost:9000/health"; then
    echo "✅ MCP Hub is healthy"
else
    echo "⚠️ MCP Hub not ready yet"
fi

echo "✅ Deployment complete!"
echo "🌐 Access your trading system at: http://$SERVER_IP:8000"
echo "📊 MCP Hub available at: http://$SERVER_IP:9000"
echo "📱 Slack notifications should now be active"

echo "🎉 AI Trading System is now running in production!"
"""

    async def deploy(self) -> bool:
        """Execute full deployment"""
        try:
            print("🚀 Starting real Hetzner Cloud deployment")
            print("=" * 60)
            
            # Create server
            server = self.create_server()
            if not server:
                return False
            
            server_id = server['id']
            
            # Wait for server to be ready
            server_ip = self.wait_for_server_ready(server_id)
            if not server_ip:
                return False
            
            # Generate deployment script
            deployment_script = self.generate_deployment_script(server_ip)
            script_path = "/Users/alexdumats/trajdar_bjorn/deploy/deploy_real_server.sh"
            
            with open(script_path, 'w') as f:
                f.write(deployment_script)
            
            os.chmod(script_path, 0o755)
            
            # Save deployment info
            deployment_info = {
                "timestamp": datetime.now().isoformat(),
                "server_id": server_id,
                "server_ip": server_ip,
                "server_name": server['name'],
                "deployment_script": script_path,
                "access_urls": {
                    "system": f"http://{server_ip}:8000",
                    "mcp_hub": f"http://{server_ip}:9000"
                }
            }
            
            info_path = "/Users/alexdumats/trajdar_bjorn/deploy/real_deployment_info.json"
            with open(info_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("=" * 60)
            print("🎯 Deployment Ready!")
            print(f"📋 Server ID: {server_id}")
            print(f"🌐 Server IP: {server_ip}")
            print(f"📜 Deployment Script: {script_path}")
            print(f"💾 Info Saved: {info_path}")
            print()
            print("Next steps:")
            print(f"1. Run: {script_path}")
            print(f"2. Access: http://{server_ip}:8000")
            print(f"3. Monitor: http://{server_ip}:9000")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

async def main():
    deployment = RealHetznerDeployment()
    success = await deployment.deploy()
    
    if success:
        print("🎉 Real server deployment preparation completed!")
    else:
        print("❌ Deployment preparation failed!")

if __name__ == "__main__":
    asyncio.run(main())