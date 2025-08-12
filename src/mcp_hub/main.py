#!/usr/bin/env python3
"""
MCP Hub Service - Central management for all MCP servers
Coordinates 16+ MCP servers for enhanced trading capabilities
"""

import asyncio
import json
import logging
import os
import subprocess
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import aiohttp
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from slack_webhook_logger import SlackWebhookLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Hub Service", version="1.0.0")

class MCPServerManager:
    def __init__(self):
        self.config_path = os.getenv("MCP_CONFIG_PATH", os.path.join(os.path.dirname(__file__), "../../config/mcp_servers.yaml"))
        self.servers = {}
        self.active_processes = {}
        self.server_health = {}
        self.slack_logger = SlackWebhookLogger("mcp_hub")
        self.load_config()
        
    def load_config(self):
        """Load MCP server configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.servers = config.get('servers', {})
                self.env_vars = config.get('environment_variables', {})
            logger.info(f"✅ Loaded {len(self.servers)} MCP server configurations")
        except Exception as e:
            logger.error(f"❌ Failed to load MCP config: {e}")
            self.servers = {}
    
    async def start_server(self, server_name: str) -> bool:
        """Start a specific MCP server"""
        if server_name not in self.servers:
            logger.error(f"❌ Server {server_name} not found in config")
            return False
        
        server_config = self.servers[server_name]
        
        try:
            if server_config['type'] == 'stdio':
                return await self._start_stdio_server(server_name, server_config)
            elif server_config['type'] == 'sse':
                return await self._start_sse_server(server_name, server_config)
            elif server_config['type'] == 'http':
                return await self._start_http_server(server_name, server_config)
            else:
                logger.error(f"❌ Unknown server type: {server_config['type']}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to start {server_name}: {e}")
            return False
    
    async def _start_stdio_server(self, server_name: str, config: Dict) -> bool:
        """Start a stdio-based MCP server"""
        try:
            env = os.environ.copy()
            env.update(self.env_vars)
            env.update(config.get('env', {}))
            
            process = subprocess.Popen(
                [config['command']] + config['args'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.active_processes[server_name] = process
            self.server_health[server_name] = {
                'status': 'starting',
                'pid': process.pid,
                'started_at': datetime.now().isoformat()
            }
            
            logger.info(f"🚀 Started {server_name} (PID: {process.pid})")
            
            # Log to Slack
            await self.slack_logger.log_activity("start", {
                "server_name": server_name,
                "server_type": config['type'],
                "pid": process.pid,
                "description": config.get('description', 'MCP Server')
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {server_name}: {e}")
            return False
    
    async def _start_sse_server(self, server_name: str, config: Dict) -> bool:
        """Start an SSE-based MCP server"""
        try:
            self.server_health[server_name] = {
                'status': 'running',
                'type': 'sse',
                'endpoint': config.get('endpoint'),
                'started_at': datetime.now().isoformat()
            }
            logger.info(f"🚀 Started SSE server {server_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start SSE server {server_name}: {e}")
            return False

    async def _start_http_server(self, server_name: str, config: Dict) -> bool:
        """Register an HTTP-based MCP server"""
        try:
            self.server_health[server_name] = {
                'status': 'running',
                'type': 'http',
                'endpoint': config.get('endpoint'),
                'started_at': datetime.now().isoformat()
            }
            logger.info(f"🚀 Registered HTTP server {server_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to register HTTP server {server_name}: {e}")
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server"""
        if server_name not in self.active_processes:
            logger.warning(f"⚠️ Server {server_name} not running")
            return False
        
        try:
            process = self.active_processes[server_name]
            process.terminate()
            process.wait(timeout=10)
            
            if process.poll() is None:
                process.kill()
            
            del self.active_processes[server_name]
            self.server_health[server_name]['status'] = 'stopped'
            
            logger.info(f"⏹️ Stopped {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop {server_name}: {e}")
            return False
    
    async def check_health(self, server_name: str) -> Dict[str, Any]:
        """Check health of a specific MCP server"""
        if server_name not in self.servers:
            return {'status': 'not_found', 'error': 'Server not configured'}
        
        config = self.servers[server_name]
        
        # For SSE servers, check endpoint availability
        if config['type'] == 'sse' or config['type'] == 'http':
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(config['endpoint'], timeout=5) as response:
                        return {
                            'status': 'healthy' if response.status == 200 else 'unhealthy',
                            'response_code': response.status
                        }
            except Exception as e:
                return {'status': 'unhealthy', 'error': str(e)}
        
        # For stdio servers, check process status
        if server_name in self.active_processes:
            process = self.active_processes[server_name]
            if process.poll() is None:
                return {'status': 'healthy', 'pid': process.pid}
            else:
                return {'status': 'stopped', 'exit_code': process.poll()}
        
        return {'status': 'not_running'}
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all configured MCP servers"""
        results = {}
        for server_name in self.servers:
            results[server_name] = await self.start_server(server_name)
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all running MCP servers"""
        results = {}
        for server_name in list(self.active_processes.keys()):
            results[server_name] = await self.stop_server(server_name)
        return results
    
    def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """Get information about a specific server"""
        if server_name not in self.servers:
            return {'error': 'Server not found'}
        
        server_config = self.servers[server_name]
        health_info = self.server_health.get(server_name, {})
        
        return {
            'name': server_name,
            'config': server_config,
            'health': health_info,
            'running': server_name in self.active_processes
        }
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all configured servers"""
        return [self.get_server_info(name) for name in self.servers.keys()]

# Global manager instance
manager = MCPServerManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_servers": len(manager.servers),
        "active_servers": len(manager.active_processes)
    }

@app.get("/servers")
async def list_servers():
    """List all configured MCP servers"""
    return manager.list_servers()

@app.get("/servers/{server_name}")
async def get_server(server_name: str):
    """Get information about a specific server"""
    return manager.get_server_info(server_name)

@app.post("/servers/{server_name}/start")
async def start_server(server_name: str):
    """Start a specific MCP server"""
    success = await manager.start_server(server_name)
    return {"success": success, "server": server_name}

@app.post("/servers/{server_name}/stop")
async def stop_server(server_name: str):
    """Stop a specific MCP server"""
    success = await manager.stop_server(server_name)
    return {"success": success, "server": server_name}

@app.get("/servers/{server_name}/health")
async def check_server_health(server_name: str):
    """Check health of a specific server"""
    return await manager.check_health(server_name)

@app.post("/servers/start-all")
async def start_all_servers():
    """Start all configured MCP servers"""
    results = await manager.start_all_servers()
    return {"results": results}

@app.post("/servers/stop-all")
async def stop_all_servers():
    """Stop all running MCP servers"""
    results = await manager.stop_all_servers()
    return {"results": results}

@app.get("/status")
async def get_status():
    """Get comprehensive status of all servers"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "total_servers": len(manager.servers),
        "active_servers": len(manager.active_processes),
        "servers": {}
    }
    
    for server_name in manager.servers:
        status["servers"][server_name] = await manager.check_health(server_name)
    
    return status

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
