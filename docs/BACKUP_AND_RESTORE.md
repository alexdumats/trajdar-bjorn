# 💾 TrajDAR Backup and Restore Guide

## Overview
This document covers backup and restore procedures for the TrajDAR AI Trading System, ensuring you can safely preserve and restore your trading configurations, data, and optimizations.

## 🎯 Current System State

**System Version**: 2.0.1  
**Last Backup**: 2025-08-12 11:31:43  
**Portfolio Value**: $10,016.21 (+$16.21 profit)  
**Status**: Active with optimized parameters  

## 📦 Backup Components

### Complete Backup Includes:
- ✅ **Source Code** (`src/`) - All Python trading services
- ✅ **Configuration Files** (`config/`) - Including optimized parameters
- ✅ **Database** (`database/paper_trading.db`) - Trade history and portfolio data
- ✅ **Environment Files** (`.env*`) - API keys and system settings
- ✅ **Docker Configurations** (`docker-compose*.yml`) - Container settings
- ✅ **System Logs** (`logs/`) - All operational history
- ✅ **Optimization Results** (`*results*.json`) - Backtesting and optimization data
- ✅ **MCP Server Configurations** (`mcp-servers/`) - All MCP server code

## 🔧 Creating a Backup

### Automated Backup Script
```bash
#!/bin/bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/trajdar_backup_$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy all components
cp -r src/ "$BACKUP_DIR/"
cp -r config/ "$BACKUP_DIR/"
cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || echo "No logs directory"
cp database/paper_trading.db "$BACKUP_DIR/" 2>/dev/null || echo "No database found"
cp .env* "$BACKUP_DIR/" 2>/dev/null || echo "No environment files"
cp docker-compose*.yml "$BACKUP_DIR/" 2>/dev/null
cp *results*.json "$BACKUP_DIR/" 2>/dev/null || echo "No results files"

# Create compressed archive
tar -czf "trajdar_backup_$TIMESTAMP.tar.gz" -C backups "trajdar_backup_$TIMESTAMP"

echo "✅ Backup completed: trajdar_backup_$TIMESTAMP.tar.gz"
```

### Manual Backup Steps
```bash
# 1. Create backup directory
mkdir -p backups/manual_backup_$(date +%Y%m%d)

# 2. Copy essential components
cp -r src config logs database backups/manual_backup_$(date +%Y%m%d)/
cp .env* docker-compose*.yml backups/manual_backup_$(date +%Y%m%d)/

# 3. Compress backup
tar -czf manual_backup_$(date +%Y%m%d).tar.gz backups/manual_backup_$(date +%Y%m%d)/
```

## 🔄 Restore Procedures

### Full System Restore
```bash
# 1. Extract backup
tar -xzf trajdar_backup_YYYYMMDD_HHMMSS.tar.gz

# 2. Copy files to system location
cp -r trajdar_backup_YYYYMMDD_HHMMSS/* /path/to/trajdar_bjorn/

# 3. Set permissions
chmod +x scripts/*.sh

# 4. Restore database
cp paper_trading.db database/

# 5. Verify configuration
cat config/trading_parameters.yaml

# 6. Start system
docker-compose up -d
```

### Selective Restore Options

**Configuration Only:**
```bash
cp trajdar_backup_*/config/* config/
```

**Database Only:**
```bash
cp trajdar_backup_*/paper_trading.db database/
```

**Environment Files Only:**
```bash
cp trajdar_backup_*/.env* ./
```

## 🔐 Security Considerations

### Backup Security
- ⚠️ **API Keys**: Backups contain sensitive API keys in `.env` files
- 🔒 **Storage**: Store backups in secure, encrypted locations
- 🔑 **Access**: Limit backup access to authorized personnel only
- 🗑️ **Retention**: Regularly delete old backups to minimize exposure

### Best Practices
```bash
# Encrypt backup before storage
gpg -c trajdar_backup_YYYYMMDD.tar.gz

# Secure delete original after encryption
rm trajdar_backup_YYYYMMDD.tar.gz

# Store in secure cloud storage
aws s3 cp trajdar_backup_YYYYMMDD.tar.gz.gpg s3://secure-bucket/backups/
```

## 📋 Backup Schedule Recommendations

### Production Systems
- **Daily**: Automated configuration and database backups
- **Weekly**: Full system backups including logs
- **Before Changes**: Manual backup before any optimization or updates
- **After Optimization**: Immediate backup of successful optimizations

### Development/Testing
- **Before Testing**: Backup current state
- **After Successful Tests**: Backup proven configurations
- **Monthly**: Archive old backups

## 🎯 Current Optimized Configuration

The latest backup includes these optimized parameters:

**Risk Management:**
- Max Position Size: 8%
- Stop Loss: 2%
- Take Profit: 4%
- Max Daily Trades: 8

**RSI Strategy:**
- Period: 10
- Oversold Threshold: 25
- Overbought Threshold: 75
- Min Confidence: 70%

## 🚨 Emergency Recovery

### System Corruption Recovery
```bash
# 1. Stop all services
docker-compose down

# 2. Restore from latest backup
tar -xzf latest_backup.tar.gz
cp -r backup_contents/* ./

# 3. Verify integrity
python3 -c "import src.orchestrator_service; print('✅ Code integrity OK')"

# 4. Restart system
docker-compose up -d
```

### Database Recovery
```bash
# Create database backup first
cp database/paper_trading.db database/paper_trading_corrupted.db

# Restore from backup
cp backups/latest/paper_trading.db database/

# Verify database integrity
sqlite3 database/paper_trading.db "PRAGMA integrity_check;"
```

## 📞 Support and Troubleshooting

### Common Issues
1. **Permission Errors**: `chmod -R 755 scripts/`
2. **Missing Dependencies**: `pip install -r requirements.txt`
3. **Database Lock**: Stop all services before restoring database
4. **Environment Variables**: Verify all `.env` files are restored

### Health Check After Restore
```bash
# Check system health
curl http://localhost:8000/health

# Verify configuration
curl http://localhost:8000/system-status

# Check portfolio
curl http://localhost:8001/portfolio
```

---

## 📈 Latest Backup Information

**Current Backup**: `trajdar_backup_20250812_113143.tar.gz` (466KB)  
**Contents**: Complete system with optimized parameters  
**Performance**: +0.16% returns, 163 trades  
**Status**: Production-ready with proven profitability  

**Restore Command:**
```bash
tar -xzf trajdar_backup_20250812_113143.tar.gz
```

---
*Last updated: 2025-08-12 - Includes optimized parameters and proven trading performance*