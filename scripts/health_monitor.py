#!/usr/bin/env python3
"""
Comprehensive Health Monitoring Script for AI Trading System
Checks health of all services and provides system-wide status
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

class HealthMonitor:
    def __init__(self):
        self.services = {
            "orchestrator": "http://localhost:8000/health",
            "portfolio": "http://localhost:8001/health", 
            "risk_manager": "http://localhost:8002/health",
            "market_analyst": "http://localhost:8003/health",
            "notification": "http://localhost:8004/health",
            "trade_executor": "http://localhost:8005/health",
            "parameter_optimizer": "http://localhost:8006/health",
            "mcp_hub": "http://localhost:9000/health"
        }
        
        self.timeout = 5  # seconds
        self.results = {}
        
    async def check_service_health(self, session: aiohttp.ClientSession, 
                                 service_name: str, url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            async with session.get(url, timeout=self.timeout) as response:
                response_time = (time.time() - start_time) * 1000  # ms
                
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "service": service_name,
                        "status": "healthy",
                        "response_time_ms": round(response_time, 2),
                        "url": url,
                        "details": health_data,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "service": service_name,
                        "status": "unhealthy",
                        "response_time_ms": round(response_time, 2),
                        "url": url,
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except asyncio.TimeoutError:
            return {
                "service": service_name,
                "status": "timeout",
                "response_time_ms": self.timeout * 1000,
                "url": url,
                "error": "Request timeout",
                "timestamp": datetime.now().isoformat()
            }
        except aiohttp.ClientConnectorError:
            return {
                "service": service_name,
                "status": "unreachable",
                "response_time_ms": 0,
                "url": url,
                "error": "Connection refused",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "response_time_ms": 0,
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services concurrently"""
        connector = aiohttp.TCPConnector(limit=20)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [
                self.check_service_health(session, service_name, url)
                for service_name, url in self.services.items()
            ]
            
            service_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            healthy_count = 0
            degraded_count = 0
            unhealthy_count = 0
            total_response_time = 0
            
            processed_results = {}
            
            for result in service_results:
                if isinstance(result, Exception):
                    continue
                    
                service_name = result["service"]
                processed_results[service_name] = result
                
                if result["status"] == "healthy":
                    healthy_count += 1
                elif result["status"] in ["timeout", "degraded"]:
                    degraded_count += 1
                else:
                    unhealthy_count += 1
                
                total_response_time += result.get("response_time_ms", 0)
            
            total_services = len(self.services)
            average_response_time = total_response_time / max(total_services, 1)
            
            # Determine overall system status
            if unhealthy_count > total_services * 0.5:
                overall_status = "critical"
            elif unhealthy_count > 0 or degraded_count > total_services * 0.3:
                overall_status = "degraded"
            elif degraded_count > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_services": total_services,
                    "healthy": healthy_count,
                    "degraded": degraded_count,
                    "unhealthy": unhealthy_count,
                    "health_percentage": (healthy_count / total_services) * 100,
                    "average_response_time_ms": round(average_response_time, 2)
                },
                "services": processed_results,
                "recommendations": self._generate_recommendations(processed_results)
            }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on health status"""
        recommendations = []
        
        unhealthy_services = [
            name for name, data in results.items() 
            if data["status"] in ["unhealthy", "unreachable", "error"]
        ]
        
        slow_services = [
            name for name, data in results.items()
            if data.get("response_time_ms", 0) > 1000
        ]
        
        if unhealthy_services:
            recommendations.append(f"Restart unhealthy services: {', '.join(unhealthy_services)}")
        
        if slow_services:
            recommendations.append(f"Investigate slow response times: {', '.join(slow_services)}")
        
        # Check for critical service failures
        critical_services = ["orchestrator", "portfolio", "risk_manager"]
        critical_down = [s for s in critical_services if s in unhealthy_services]
        
        if critical_down:
            recommendations.append(f"URGENT: Critical services down - {', '.join(critical_down)}")
        
        if not recommendations:
            recommendations.append("All services are healthy")
        
        return recommendations
    
    def format_output(self, results: Dict[str, Any], format_type: str = "console") -> str:
        """Format health check results for different outputs"""
        
        if format_type == "json":
            return json.dumps(results, indent=2)
        
        elif format_type == "console":
            output = []
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️", 
                "degraded": "🟡",
                "critical": "❌"
            }
            
            emoji = status_emoji.get(results["system_status"], "❓")
            output.append(f"\n{emoji} AI Trading System Health Check")
            output.append(f"Overall Status: {results['system_status'].upper()}")
            output.append(f"Timestamp: {results['timestamp']}")
            
            # Summary
            summary = results["summary"]
            output.append(f"\n📊 System Summary:")
            output.append(f"  Services: {summary['healthy']}/{summary['total_services']} healthy")
            output.append(f"  Health: {summary['health_percentage']:.1f}%")
            output.append(f"  Avg Response: {summary['average_response_time_ms']:.1f}ms")
            
            # Service details
            output.append(f"\n🔧 Service Status:")
            for service_name, service_data in results["services"].items():
                status_icon = "✅" if service_data["status"] == "healthy" else "❌"
                response_time = service_data.get("response_time_ms", 0)
                output.append(f"  {status_icon} {service_name}: {service_data['status']} ({response_time:.1f}ms)")
                
                if service_data["status"] != "healthy":
                    error = service_data.get("error", "Unknown error")
                    output.append(f"    Error: {error}")
            
            # Recommendations
            if results["recommendations"]:
                output.append(f"\n💡 Recommendations:")
                for rec in results["recommendations"]:
                    output.append(f"  • {rec}")
            
            return "\n".join(output)
        
        elif format_type == "slack":
            status_emoji = {
                "healthy": ":white_check_mark:",
                "warning": ":warning:",
                "degraded": ":large_yellow_circle:", 
                "critical": ":x:"
            }
            
            emoji = status_emoji.get(results["system_status"], ":question:")
            
            message = f"{emoji} *AI Trading System Health Report*\n"
            message += f"*Status:* {results['system_status'].upper()}\n"
            message += f"*Time:* {results['timestamp']}\n\n"
            
            summary = results["summary"]
            message += f"*📊 Summary:*\n"
            message += f"• Services: {summary['healthy']}/{summary['total_services']} healthy\n"
            message += f"• Health: {summary['health_percentage']:.1f}%\n"
            message += f"• Avg Response: {summary['average_response_time_ms']:.1f}ms\n\n"
            
            unhealthy = [name for name, data in results["services"].items() 
                        if data["status"] != "healthy"]
            
            if unhealthy:
                message += f"*⚠️ Issues:*\n"
                for service in unhealthy:
                    data = results["services"][service]
                    message += f"• {service}: {data['status']} - {data.get('error', 'Unknown')}\n"
            
            return message

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading System Health Monitor")
    parser.add_argument("--format", choices=["console", "json", "slack"], 
                       default="console", help="Output format")
    parser.add_argument("--continuous", action="store_true", 
                       help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=30,
                       help="Interval for continuous monitoring (seconds)")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor()
    
    if args.continuous:
        print(f"Starting continuous monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                results = await monitor.check_all_services()
                output = monitor.format_output(results, args.format)
                
                if args.output:
                    with open(args.output, "w") as f:
                        f.write(output)
                    print(f"Health report written to {args.output}")
                else:
                    print(output)
                
                # Exit with error code if system is critical
                if results["system_status"] == "critical":
                    print("\n⚠️ CRITICAL: System health is critical!")
                    if not args.continuous:
                        sys.exit(1)
                
                await asyncio.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        # Single check
        results = await monitor.check_all_services()
        output = monitor.format_output(results, args.format)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Health report written to {args.output}")
        else:
            print(output)
        
        # Exit with error code if system is critical
        if results["system_status"] == "critical":
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())