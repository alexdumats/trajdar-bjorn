# Performance Metrics Framework - Integration Guidelines

## Overview

This document provides comprehensive guidelines for integrating the Performance Metrics Framework into existing trading systems. It includes step-by-step instructions, code examples, API reference documentation, and common implementation scenarios to facilitate seamless adoption.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Basic Configuration](#basic-configuration)
4. [Core Integration Patterns](#core-integration-patterns)
5. [API Reference](#api-reference)
6. [MCP Server Integration](#mcp-server-integration)
7. [Common Implementation Scenarios](#common-implementation-scenarios)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Prerequisites

Before integrating the Performance Metrics Framework, ensure your system meets the following requirements:

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 50GB disk space for database and reports
- Network access to MCP servers

### Required Packages

```
numpy>=1.20.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=0.24.0
aiohttp>=3.7.0
asyncio>=3.4.3
```

### Database Requirements

- SQLite 3.35.0 or higher
- Database schema compatible with the framework (see [Database Schema](#database-schema))

## Installation

### Option 1: Using pip

```bash
pip install performance-metrics-framework
```

### Option 2: From Source

```bash
git clone https://github.com/organization/performance-metrics-framework.git
cd performance-metrics-framework
pip install -e .
```

### Option 3: Using Docker

```bash
docker pull organization/performance-metrics-framework:latest
docker run -d -p 8080:8080 -v /path/to/data:/app/data organization/performance-metrics-framework:latest
```

## Basic Configuration

### Environment Variables

Create a `.env` file in your project root with the following variables:

```
DB_PATH=database/paper_trading.db
REPORTS_DIR=reports
LOOKBACK_DAYS=30
ARXIV_MCP_URL=http://localhost:8301
SLACK_MCP_URL=http://localhost:8302
MEMORY_MCP_URL=http://localhost:8303
TIME_MCP_URL=http://localhost:8304
SQLITE_MCP_URL=http://localhost:8305
```

### Configuration File

Alternatively, create a `config.yaml` file:

```yaml
database:
  path: database/paper_trading.db
  backup_dir: database/backups

reporting:
  reports_dir: reports
  formats:
    - markdown
    - json
    - html

analysis:
  lookback_days: 30
  profit_targets:
    - 0.5
    - 1.0
    - 1.5
    - 2.0
    - 3.0

mcp_servers:
  arxiv:
    url: http://localhost:8301
    papers_dir: mcp-servers/arxiv-mcp-server/papers
  slack:
    url: http://localhost:8302
    default_channel: "#profit-monitoring"
  memory:
    url: http://localhost:8303
  time:
    url: http://localhost:8304
    default_timezone: UTC
  sqlite:
    url: http://localhost:8305
```

### Database Schema

Ensure your database includes the following tables:

```sql
-- Paper trades table
CREATE TABLE paper_trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME,
    pnl REAL,
    pnl_percentage REAL,
    execution_time_ms INTEGER,
    expected_price REAL,
    actual_price REAL
);

-- Portfolio snapshots table
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    total_value REAL NOT NULL,
    cash_balance REAL NOT NULL,
    equity_value REAL NOT NULL,
    margin_used REAL,
    margin_available REAL
);

-- Profit alerts table
CREATE TABLE profit_alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    actual_value REAL NOT NULL,
    alert_time DATETIME NOT NULL,
    response_time DATETIME,
    predicted_profit_pct REAL,
    actual_profit_pct REAL
);

-- System events table
CREATE TABLE system_events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    component TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL
);
```

## Core Integration Patterns

### Pattern 1: Standalone Analysis

Use the framework as a standalone analysis tool that processes your trading data periodically.

```python
import asyncio
from performance_metrics_framework import PerformanceMetricsFramework

async def run_standalone_analysis():
    # Initialize the framework
    framework = PerformanceMetricsFramework()
    
    # Calculate metrics for each profit target
    for target in framework.profit_targets:
        await framework.calculate_metrics_with_mcp(target)
    
    # Compare profit targets
    comparison = await framework.compare_profit_targets_with_mcp()
    
    # Generate report
    report_path = await framework.generate_report("markdown")
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_standalone_analysis())
```

### Pattern 2: Embedded Integration

Embed the framework directly into your trading system for real-time analysis.

```python
import asyncio
from trading_system import TradingSystem
from performance_metrics_framework import PerformanceMetricsFramework

class EnhancedTradingSystem(TradingSystem):
    def __init__(self):
        super().__init__()
        self.metrics_framework = PerformanceMetricsFramework()
    
    async def after_trading_day(self):
        # Run standard end-of-day procedures
        await super().after_trading_day()
        
        # Calculate performance metrics
        for target in self.metrics_framework.profit_targets:
            await self.metrics_framework.calculate_metrics_with_mcp(target)
        
        # Compare profit targets
        comparison = await self.metrics_framework.compare_profit_targets_with_mcp()
        
        # Generate report
        report_path = await self.metrics_framework.generate_report("markdown")
        
        # Send notification
        await self.metrics_framework.send_slack_notification(
            channel="#daily-reports",
            message=f"Daily performance report available: {report_path}",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Daily Performance Report"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Best profit target: {comparison.get('best_target')}%"
                    }
                }
            ]
        )

if __name__ == "__main__":
    trading_system = EnhancedTradingSystem()
    asyncio.run(trading_system.start())
```

### Pattern 3: Microservice Architecture

Deploy the framework as a microservice that other components can query.

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
from performance_metrics_framework import PerformanceMetricsFramework

app = FastAPI()
framework = PerformanceMetricsFramework()

class AnalysisRequest(BaseModel):
    profit_targets: list[float] = [0.5, 1.0, 1.5, 2.0, 3.0]
    lookback_days: int = 30
    output_format: str = "json"

@app.post("/analyze")
async def analyze_performance(request: AnalysisRequest, background_tasks: BackgroundTasks):
    # Update framework configuration
    framework.profit_targets = request.profit_targets
    framework.lookback_days = request.lookback_days
    
    # Start analysis in background
    background_tasks.add_task(run_analysis, request.output_format)
    
    return {"status": "Analysis started", "job_id": "job-123"}

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    # In a real implementation, you would retrieve the results for the specific job
    return {
        "job_id": job_id,
        "status": "completed",
        "best_target": framework.comparative_results.get("best_target"),
        "metrics": framework.metrics
    }

async def run_analysis(output_format: str):
    # Calculate metrics for each profit target
    for target in framework.profit_targets:
        await framework.calculate_metrics_with_mcp(target)
    
    # Compare profit targets
    await framework.compare_profit_targets_with_mcp()
    
    # Generate report
    await framework.generate_report(output_format)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Reference

### PerformanceMetricsFramework Class

#### Constructor

```python
def __init__(self):
    """Initialize the performance metrics framework"""
```

#### Core Methods

```python
async def calculate_metrics_with_mcp(self, profit_target_pct: float = 1.0) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics for a given profit target using MCP servers"""
```

```python
async def compare_profit_targets_with_mcp(self) -> Dict[str, Any]:
    """Compare different profit target percentages using MCP servers"""
```

```python
async def generate_report(self, output_format: str = "markdown") -> str:
    """Generate a performance report in the specified format"""
```

```python
async def gather_research_on_profit_targets(self) -> Dict[str, Any]:
    """Gather research papers on profit targets and trading performance metrics"""
```

#### MCP Server Integration Methods

```python
async def send_slack_notification(self, channel: str, message: str, blocks: Optional[List[Dict[str, Any]]] = None) -> bool:
    """Send a notification to Slack using the Slack MCP server"""
```

```python
async def store_insight_in_memory(self, entity_name: str, entity_type: str, observations: List[str]) -> bool:
    """Store an insight in the Memory MCP server"""
```

```python
async def create_relation_in_memory(self, from_entity: str, to_entity: str, relation_type: str) -> bool:
    """Create a relation between entities in the Memory MCP server"""
```

```python
async def get_current_time(self, timezone: str = "UTC") -> Optional[str]:
    """Get current time in a specific timezone using the Time MCP server"""
```

```python
async def execute_sqlite_query(self, query: str, is_read: bool = True) -> Optional[List[Dict[str, Any]]]:
    """Execute a query on the SQLite database using the SQLite MCP server"""
```

```python
async def append_business_insight(self, insight: str) -> bool:
    """Append a business insight to the memo using the SQLite MCP server"""
```

```python
async def search_arxiv_papers(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search for relevant papers on arXiv using the MCP server"""
```

```python
async def read_arxiv_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
    """Read a paper from arXiv using the MCP server"""
```

## MCP Server Integration

### Setting Up MCP Servers

#### ArXiv MCP Server

```bash
cd mcp-servers
git clone https://github.com/organization/arxiv-mcp-server.git
cd arxiv-mcp-server
npm install
npm start
```

#### Slack MCP Server

```bash
cd mcp-servers
git clone https://github.com/organization/slack-mcp-server.git
cd slack-mcp-server
npm install
npm start
```

#### Memory MCP Server

```bash
cd mcp-servers
git clone https://github.com/organization/memory-mcp-server.git
cd memory-mcp-server
npm install
npm start
```

#### Time MCP Server

```bash
cd mcp-servers
git clone https://github.com/organization/time-mcp-server.git
cd time-mcp-server
npm install
npm start
```

#### SQLite MCP Server

```bash
cd mcp-servers
git clone https://github.com/organization/sqlite-mcp-server.git
cd sqlite-mcp-server
npm install
npm start
```

### Configuring MCP Server Connections

Update your `.env` file or `config.yaml` with the appropriate URLs for each MCP server. If you're running the servers on different machines, use the appropriate IP addresses or hostnames.

## Common Implementation Scenarios

### Scenario 1: Daily Performance Analysis

```python
import asyncio
import schedule
import time
from performance_metrics_framework import PerformanceMetricsFramework

async def run_daily_analysis():
    print(f"Starting daily analysis at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize the framework
    framework = PerformanceMetricsFramework()
    
    # Calculate metrics for each profit target
    for target in framework.profit_targets:
        await framework.calculate_metrics_with_mcp(target)
    
    # Compare profit targets
    comparison = await framework.compare_profit_targets_with_mcp()
    
    # Generate report
    report_path = await framework.generate_report("markdown")
    
    print(f"Daily analysis completed. Report: {report_path}")
    
    # Send notification
    await framework.send_slack_notification(
        channel="#daily-reports",
        message=f"Daily performance report available: {report_path}"
    )

def schedule_daily_analysis():
    asyncio.run(run_daily_analysis())

if __name__ == "__main__":
    # Schedule daily analysis at 00:30 UTC
    schedule.every().day.at("00:30").do(schedule_daily_analysis)
    
    print("Scheduler started. Waiting for scheduled tasks...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### Scenario 2: Real-time Dashboard Integration

```python
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from performance_metrics_framework import PerformanceMetricsFramework

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

framework = PerformanceMetricsFramework()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initial data load
    for target in framework.profit_targets:
        metrics = await framework.calculate_metrics_with_mcp(target)
        await websocket.send_json({
            "type": "metrics_update",
            "profit_target": target,
            "metrics": metrics
        })
    
    comparison = await framework.compare_profit_targets_with_mcp()
    await websocket.send_json({
        "type": "comparison_update",
        "comparison": comparison
    })
    
    # Real-time updates
    try:
        while True:
            # Wait for 5 minutes before updating
            await asyncio.sleep(300)
            
            # Update metrics for best target
            best_target = comparison.get("best_target", 1.5)
            metrics = await framework.calculate_metrics_with_mcp(best_target)
            
            await websocket.send_json({
                "type": "metrics_update",
                "profit_target": best_target,
                "metrics": metrics
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/")
async def get_dashboard():
    return {"message": "Access the dashboard at /static/dashboard.html"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Scenario 3: Automated Trading Strategy Optimization

```python
import asyncio
from performance_metrics_framework import PerformanceMetricsFramework
from trading_system import TradingSystem, Strategy

class AdaptiveStrategy(Strategy):
    def __init__(self, profit_target: float = 1.5):
        super().__init__()
        self.profit_target = profit_target
    
    def set_profit_target(self, target: float):
        self.profit_target = target
        print(f"Strategy profit target updated to {target}%")

async def optimize_trading_strategy():
    # Initialize the framework and trading system
    framework = PerformanceMetricsFramework()
    trading_system = TradingSystem()
    strategy = AdaptiveStrategy()
    trading_system.set_strategy(strategy)
    
    while True:
        # Calculate metrics for each profit target
        for target in framework.profit_targets:
            await framework.calculate_metrics_with_mcp(target)
        
        # Compare profit targets
        comparison = await framework.compare_profit_targets_with_mcp()
        
        # Get best profit target
        best_target = comparison.get("best_target", 1.5)
        
        # Update strategy
        strategy.set_profit_target(best_target)
        
        # Store insight
        await framework.store_insight_in_memory(
            entity_name="strategy_optimization",
            entity_type="optimization",
            observations=[
                f"Optimized profit target: {best_target}%",
                f"Optimization timestamp: {await framework.get_current_time('UTC')}",
                f"Previous targets analyzed: {', '.join([str(t) for t in framework.profit_targets])}%"
            ]
        )
        
        # Wait for next optimization cycle (4 hours)
        await asyncio.sleep(4 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(optimize_trading_strategy())
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: MCP Server Connection Failures

**Symptoms:**
- Error logs showing connection timeouts
- Missing data in reports
- Failed notifications

**Solutions:**
1. Verify MCP server is running: `curl http://localhost:8301/health`
2. Check network connectivity: `ping localhost`
3. Verify correct URL in configuration
4. Check for firewall blocking connections
5. Increase connection timeout settings

#### Issue: Database Access Errors

**Symptoms:**
- SQLite errors in logs
- Missing or incomplete metrics
- Failed report generation

**Solutions:**
1. Verify database file exists: `ls -la database/paper_trading.db`
2. Check file permissions: `chmod 644 database/paper_trading.db`
3. Verify database schema matches requirements
4. Check disk space: `df -h`
5. Repair database if corrupted: `sqlite3 database/paper_trading.db "PRAGMA integrity_check;"`

#### Issue: Memory Usage Problems

**Symptoms:**
- Out of memory errors
- System slowdowns
- Unexpected process termination

**Solutions:**
1. Reduce lookback period for analysis
2. Implement batch processing for large datasets
3. Increase system memory allocation
4. Add memory usage checkpoints in critical paths
5. Optimize data structures for memory efficiency

### Logging and Debugging

Enable detailed logging by setting the log level in your configuration:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/performance_metrics_debug.log"),
        logging.StreamHandler()
    ]
)
```

## Best Practices

### Performance Optimization

1. **Batch Processing**: Process large datasets in batches to manage memory usage
2. **Caching**: Cache frequently accessed data to reduce database load
3. **Asynchronous Processing**: Use async/await pattern for I/O-bound operations
4. **Database Indexing**: Ensure proper indexes on timestamp and other frequently queried columns
5. **Report Compression**: Compress and archive old reports to save disk space

### Security Considerations

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **Access Control**: Implement role-based access for report generation and analysis
3. **Input Validation**: Validate all inputs, especially SQL queries
4. **Secure Communications**: Use HTTPS for MCP server communications
5. **Audit Logging**: Maintain comprehensive logs of all operations

### Integration Patterns

1. **Loose Coupling**: Minimize dependencies between the framework and your trading system
2. **Event-Driven Architecture**: Use events to trigger analysis and reporting
3. **Microservices**: Deploy as a separate service for better scalability
4. **API Gateway**: Use an API gateway for centralized access control
5. **Circuit Breakers**: Implement circuit breakers for MCP server calls

### Monitoring and Alerting

1. **Health Checks**: Implement health check endpoints for all components
2. **Metrics Collection**: Collect and monitor system metrics
3. **Alerting**: Set up alerts for critical failures
4. **Dashboard**: Create a monitoring dashboard for system health
5. **Log Analysis**: Regularly analyze logs for patterns and issues