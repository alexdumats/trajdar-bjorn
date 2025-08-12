# 🚀 Hetzner Deployment Guide

## Quick Deployment Steps

### 1. Prerequisites

**On Your Local Machine:**
- SSH access to your Hetzner server
- SSH key configured for root access

**Your Hetzner Server Requirements:**
- Ubuntu 20.04+ / Debian 11+
- 4+ GB RAM
- 20+ GB storage
- Public IP address

### 2. Initial Server Setup

```bash
# Set your server IP
export SERVER_IP=YOUR_HETZNER_IP_HERE

# Run initial server setup
./scripts/deploy_hetzner.sh setup
```

This will:
- Install Docker, Docker Compose
- Install Ollama with AI models (mistral, phi3)
- Configure firewall (UFW)
- Set up fail2ban security
- Create application directories

### 3. Configure Environment Variables

```bash
# Copy and edit environment template
cp .env.production.template .env
nano .env
```

**Required Configuration:**
- `SLACK_BOT_TOKEN` - For notifications (see setup guide below)
- `TRADING_SYMBOL` - Trading pair (default: BTCUSDT)
- `STARTING_BALANCE` - Initial balance for paper trading

**Optional Configuration:**
- Notion integration for documentation
- Binance API for real market data
- Custom trading parameters

### 4. Deploy Application

```bash
# Deploy to server and start services
./scripts/deploy_hetzner.sh deploy
```

This will:
- Upload all code to `/opt/ai-trading-system/`
- Create production Docker containers
- Start all trading services
- Configure health monitoring

### 5. Verify Deployment

```bash
# Check system status
./scripts/deploy_hetzner.sh status

# View logs
./scripts/deploy_hetzner.sh logs orchestrator
```

## 🔧 Slack Setup (Required)

### Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "AI Trading Bot", choose your workspace

### Configure Bot Permissions
1. Go to "OAuth & Permissions"
2. Add Bot Token Scopes:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`

### Install App
1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
3. Add to your `.env` file as `SLACK_BOT_TOKEN`

### Create Channels
Create these Slack channels:
- `#trading-alerts` - For trade notifications
- `#general` - For system messages

## 🖥️ Service URLs

Once deployed, access your services at:

- **Main Dashboard**: `http://YOUR_SERVER_IP:8000/system-status`
- **Portfolio Service**: `http://YOUR_SERVER_IP:8001/portfolio`
- **Risk Manager**: `http://YOUR_SERVER_IP:8002/health`
- **Market Analyst**: `http://YOUR_SERVER_IP:8003/health`
- **Notifications**: `http://YOUR_SERVER_IP:8004/health`

## 📊 Management Commands

```bash
# Start services
./scripts/deploy_hetzner.sh start

# Stop services  
./scripts/deploy_hetzner.sh stop

# Update deployment
./scripts/deploy_hetzner.sh update

# View service logs
./scripts/deploy_hetzner.sh logs [service-name]

# Create backup
./scripts/deploy_hetzner.sh backup

# Check status
./scripts/deploy_hetzner.sh status
```

## 🔍 Monitoring

### Health Monitoring
```bash
# SSH to your server
ssh root@YOUR_SERVER_IP

# Run monitoring script
/opt/ai-trading-system/scripts/monitor_system.sh

# Continuous monitoring
/opt/ai-trading-system/scripts/monitor_system.sh watch
```

### Service Health Checks
All services provide health endpoints:
- `GET /health` - Service health status
- `GET /metrics` - Performance metrics (if enabled)

### Log Monitoring
Logs are automatically rotated and stored in:
- Container logs: `docker-compose logs -f`
- Application logs: `/opt/ai-trading-system/logs/`

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker status
docker ps

# Check service logs
docker-compose -f docker-compose.production.yml logs [service]

# Restart specific service
docker-compose -f docker-compose.production.yml restart [service]
```

**Ollama not responding:**
```bash
# Check Ollama status
systemctl status ollama

# Restart Ollama
systemctl restart ollama

# Check models
ollama list
```

**Database issues:**
```bash
# Check database file
ls -la /opt/ai-trading-system/database/

# Backup database
cp database/paper_trading.db database/backup_$(date +%Y%m%d).db
```

**Memory issues:**
```bash
# Check memory usage
free -h

# Check which containers use most memory
docker stats

# Restart system if needed
docker-compose -f docker-compose.production.yml restart
```

## 🔒 Security Considerations

### Firewall Configuration
The deployment automatically configures UFW firewall:
- SSH (22) - Allowed
- HTTP (80) - Allowed  
- HTTPS (443) - Allowed
- Trading services (8000-8010) - Allowed
- Ollama (11434) - Allowed

### API Security
- All external API keys should be kept secure
- Use read-only API keys where possible
- Regularly rotate API credentials
- Monitor for unusual API usage

### Server Security
- Keep system updated: `apt update && apt upgrade`
- Monitor failed login attempts with fail2ban
- Consider changing default SSH port
- Use SSH keys instead of passwords

## 📈 Production Optimization

### Performance Tuning
```bash
# Increase file limits for containers
echo "fs.file-max = 100000" >> /etc/sysctl.conf

# Optimize Docker for production
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' > /etc/docker/daemon.json

# Restart Docker
systemctl restart docker
```

### Resource Monitoring
- Monitor CPU usage (should stay below 80%)
- Monitor memory usage (keep 2GB+ free)
- Monitor disk space (keep 20%+ free)
- Set up alerts for resource thresholds

### Backup Strategy
```bash
# Set up automated backups (cron job)
0 2 * * * /opt/ai-trading-system/scripts/deploy_hetzner.sh backup

# Store backups off-server for safety
# Consider using Hetzner Storage Box or other cloud storage
```

## 🆘 Support

### Getting Help
1. Check service logs first
2. Run system health check
3. Review this deployment guide
4. Check GitHub issues

### Emergency Recovery
```bash
# Complete system restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Restore from backup if needed
cp database/backup_YYYYMMDD.db database/paper_trading.db
```

---

**🎉 Your AI Trading System is now running on Hetzner!**

Monitor your system regularly and enjoy automated trading! 🚀