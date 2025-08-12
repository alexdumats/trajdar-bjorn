#!/bin/bash
"""
Setup Cron Jobs for AI Trading System Maintenance
Creates scheduled tasks for regular system cleanup and maintenance
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🔧 Setting up AI Trading System Maintenance Cron Jobs${NC}"
echo "Project root: $PROJECT_ROOT"

# Function to check if cron service is running
check_cron_service() {
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet cron; then
            echo -e "${GREEN}✅ Cron service is running${NC}"
            return 0
        else
            echo -e "${RED}❌ Cron service is not running${NC}"
            return 1
        fi
    elif command -v service &> /dev/null; then
        if service cron status &> /dev/null; then
            echo -e "${GREEN}✅ Cron service is running${NC}"
            return 0
        else
            echo -e "${RED}❌ Cron service is not running${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ Cannot determine cron service status${NC}"
        return 0
    fi
}

# Function to backup current crontab
backup_crontab() {
    local backup_file="$PROJECT_ROOT/logs/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    
    mkdir -p "$PROJECT_ROOT/logs"
    
    if crontab -l > "$backup_file" 2>/dev/null; then
        echo -e "${GREEN}✅ Current crontab backed up to: $backup_file${NC}"
    else
        echo -e "${YELLOW}⚠️ No existing crontab to backup${NC}"
        touch "$backup_file"
    fi
}

# Function to create cron jobs
setup_cron_jobs() {
    local temp_cron=$(mktemp)
    
    # Get existing crontab (if any)
    crontab -l 2>/dev/null > "$temp_cron" || true
    
    # Remove existing trading system cron jobs (marked with comments)
    sed -i '/# AI Trading System/d' "$temp_cron" 2>/dev/null || true
    sed -i '/cleanup_system.py/d' "$temp_cron" 2>/dev/null || true
    sed -i '/health_monitor.py/d' "$temp_cron" 2>/dev/null || true
    
    echo "" >> "$temp_cron"
    echo "# AI Trading System - Automated Maintenance Jobs" >> "$temp_cron"
    echo "# Generated on $(date)" >> "$temp_cron"
    
    # Daily cleanup at 2:00 AM
    echo "0 2 * * * cd $PROJECT_ROOT && python3 scripts/cleanup_system.py --log-max-age 30 --backtest-max-age 60 >> logs/cron_cleanup.log 2>&1 # AI Trading System - Daily cleanup" >> "$temp_cron"
    
    # Weekly deep cleanup on Sundays at 3:00 AM
    echo "0 3 * * 0 cd $PROJECT_ROOT && python3 scripts/cleanup_system.py --log-max-age 7 --backtest-max-age 30 >> logs/cron_cleanup_weekly.log 2>&1 # AI Trading System - Weekly deep cleanup" >> "$temp_cron"
    
    # Health check every 5 minutes (only log errors)
    echo "*/5 * * * * cd $PROJECT_ROOT && python3 scripts/health_monitor.py --format json --output logs/health_status.json 2>> logs/cron_health_errors.log # AI Trading System - Health monitoring" >> "$temp_cron"
    
    # Database vacuum every Sunday at 4:00 AM
    echo "0 4 * * 0 cd $PROJECT_ROOT && python3 scripts/cleanup_system.py --db-only >> logs/cron_db_vacuum.log 2>&1 # AI Trading System - Database maintenance" >> "$temp_cron"
    
    # Temp files cleanup every 6 hours
    echo "0 */6 * * * cd $PROJECT_ROOT && python3 scripts/cleanup_system.py --temp-only >> logs/cron_temp_cleanup.log 2>&1 # AI Trading System - Temp cleanup" >> "$temp_cron"
    
    # Install the new crontab
    if crontab "$temp_cron"; then
        echo -e "${GREEN}✅ Cron jobs installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install cron jobs${NC}"
        rm -f "$temp_cron"
        return 1
    fi
    
    rm -f "$temp_cron"
    return 0
}

# Function to show scheduled jobs
show_cron_jobs() {
    echo -e "\n${BLUE}📅 Scheduled Maintenance Jobs:${NC}"
    echo "=================================="
    
    echo -e "${YELLOW}Daily Cleanup:${NC} 2:00 AM - Clean logs older than 30 days, backtest results older than 60 days"
    echo -e "${YELLOW}Weekly Deep Cleanup:${NC} Sunday 3:00 AM - Aggressive cleanup with shorter retention"
    echo -e "${YELLOW}Health Monitoring:${NC} Every 5 minutes - Check system health and log status"
    echo -e "${YELLOW}Database Maintenance:${NC} Sunday 4:00 AM - Vacuum databases to reclaim space"
    echo -e "${YELLOW}Temp File Cleanup:${NC} Every 6 hours - Remove temporary files and caches"
    
    echo -e "\n${BLUE}📄 Log Files:${NC}"
    echo "- logs/cron_cleanup.log - Daily cleanup logs"
    echo "- logs/cron_cleanup_weekly.log - Weekly cleanup logs"
    echo "- logs/cron_health_errors.log - Health monitoring errors"
    echo "- logs/cron_db_vacuum.log - Database maintenance logs"
    echo "- logs/cron_temp_cleanup.log - Temp cleanup logs"
    echo "- logs/health_status.json - Current system health status"
}

# Function to create log rotation config
setup_log_rotation() {
    local logrotate_conf="/etc/logrotate.d/ai-trading-system"
    
    echo -e "\n${BLUE}📁 Setting up log rotation configuration${NC}"
    
    # Create logrotate configuration
    cat > "/tmp/ai-trading-system-logrotate" << EOF
$PROJECT_ROOT/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $(whoami) $(id -gn)
}

$PROJECT_ROOT/logs/cron_*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    copytruncate
    su $(whoami) $(id -gn)
}
EOF

    if sudo cp "/tmp/ai-trading-system-logrotate" "$logrotate_conf" 2>/dev/null; then
        echo -e "${GREEN}✅ Log rotation configuration installed${NC}"
        sudo chown root:root "$logrotate_conf"
        sudo chmod 644 "$logrotate_conf"
    else
        echo -e "${YELLOW}⚠️ Could not install system log rotation (sudo required)${NC}"
        echo "You can manually copy /tmp/ai-trading-system-logrotate to /etc/logrotate.d/"
    fi
    
    rm -f "/tmp/ai-trading-system-logrotate"
}

# Function to remove cron jobs
remove_cron_jobs() {
    echo -e "${YELLOW}🗑️ Removing AI Trading System cron jobs${NC}"
    
    local temp_cron=$(mktemp)
    
    # Get existing crontab
    if crontab -l 2>/dev/null > "$temp_cron"; then
        # Remove trading system cron jobs
        sed -i '/# AI Trading System/d' "$temp_cron"
        sed -i '/cleanup_system.py/d' "$temp_cron"
        sed -i '/health_monitor.py/d' "$temp_cron"
        
        # Install cleaned crontab
        if crontab "$temp_cron"; then
            echo -e "${GREEN}✅ AI Trading System cron jobs removed${NC}"
        else
            echo -e "${RED}❌ Failed to remove cron jobs${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ No crontab found${NC}"
    fi
    
    rm -f "$temp_cron"
}

# Function to test scripts
test_scripts() {
    echo -e "\n${BLUE}🧪 Testing maintenance scripts${NC}"
    
    # Test cleanup script
    echo -e "${YELLOW}Testing cleanup script (dry run)...${NC}"
    if python3 "$SCRIPT_DIR/cleanup_system.py" --dry-run; then
        echo -e "${GREEN}✅ Cleanup script test passed${NC}"
    else
        echo -e "${RED}❌ Cleanup script test failed${NC}"
        return 1
    fi
    
    # Test health monitor
    echo -e "${YELLOW}Testing health monitor...${NC}"
    if python3 "$SCRIPT_DIR/health_monitor.py" --format console; then
        echo -e "${GREEN}✅ Health monitor test passed${NC}"
    else
        echo -e "${RED}❌ Health monitor test failed${NC}"
        return 1
    fi
    
    return 0
}

# Main function
main() {
    local action="${1:-install}"
    
    case "$action" in
        "install"|"setup")
            echo -e "${BLUE}📋 Installing AI Trading System maintenance cron jobs${NC}"
            
            # Check prerequisites
            if ! check_cron_service; then
                echo -e "${RED}❌ Cron service is required but not running${NC}"
                exit 1
            fi
            
            # Test scripts first
            if ! test_scripts; then
                echo -e "${RED}❌ Script tests failed. Please fix issues before installing cron jobs.${NC}"
                exit 1
            fi
            
            # Backup existing crontab
            backup_crontab
            
            # Setup cron jobs
            if setup_cron_jobs; then
                setup_log_rotation
                show_cron_jobs
                echo -e "\n${GREEN}✅ Maintenance cron jobs installed successfully!${NC}"
                echo -e "${BLUE}💡 Tip: Check logs in $PROJECT_ROOT/logs/ to monitor maintenance activities${NC}"
            else
                echo -e "${RED}❌ Failed to setup cron jobs${NC}"
                exit 1
            fi
            ;;
            
        "remove"|"uninstall")
            remove_cron_jobs
            echo -e "${GREEN}✅ Cron jobs removed${NC}"
            ;;
            
        "show"|"list")
            echo -e "${BLUE}📋 Current AI Trading System cron jobs:${NC}"
            crontab -l 2>/dev/null | grep -A 10 -B 2 "AI Trading System" || echo "No AI Trading System cron jobs found"
            ;;
            
        "test")
            test_scripts
            ;;
            
        "help"|*)
            echo "Usage: $0 [install|remove|show|test|help]"
            echo ""
            echo "Commands:"
            echo "  install  - Install maintenance cron jobs (default)"
            echo "  remove   - Remove AI Trading System cron jobs"
            echo "  show     - Show current cron jobs"
            echo "  test     - Test maintenance scripts"
            echo "  help     - Show this help message"
            ;;
    esac
}

# Run main function with all arguments
main "$@"