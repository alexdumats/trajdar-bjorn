#!/bin/bash

# AI Trading System - Hetzner Server Deployment Script
# Deploys the complete AI trading system to Hetzner server

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_USER=${DEPLOYMENT_USER:-root}
SERVER_IP=${SERVER_IP}
PROJECT_NAME="ai-trading-system"
REMOTE_PATH="/opt/$PROJECT_NAME"

echo -e "${CYAN}🚀 AI Trading System - Hetzner Deployment${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [SERVER_IP]"
    echo ""
    echo "Commands:"
    echo "  setup     Setup server environment and dependencies"
    echo "  deploy    Deploy application and start services"
    echo "  update    Update existing deployment"
    echo "  start     Start all services"
    echo "  stop      Stop all services"
    echo "  status    Check deployment status"
    echo "  logs      View service logs"
    echo "  backup    Backup database and configuration"
    echo ""
    echo "Environment Variables:"
    echo "  SERVER_IP          Hetzner server IP address"
    echo "  DEPLOYMENT_USER    SSH user (default: root)"
    echo "  SSH_KEY_PATH       Path to SSH private key"
    echo ""
    echo "Examples:"
    echo "  SERVER_IP=1.2.3.4 $0 setup"
    echo "  SERVER_IP=1.2.3.4 $0 deploy"
    echo "  SERVER_IP=1.2.3.4 $0 status"
}

# Validate inputs
validate_inputs() {
    if [[ -z "$SERVER_IP" ]]; then
        echo -e "${RED}❌ SERVER_IP environment variable is required${NC}"
        echo "Example: SERVER_IP=1.2.3.4 $0 setup"
        exit 1
    fi
    
    if ! command -v ssh &> /dev/null; then
        echo -e "${RED}❌ SSH client not found${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Deployment Configuration:${NC}"
    echo -e "  Server IP: $SERVER_IP"
    echo -e "  User: $DEPLOYMENT_USER"
    echo -e "  Remote Path: $REMOTE_PATH"
    echo ""
}

# Test SSH connection
test_ssh_connection() {
    echo -e "${BLUE}🔍 Testing SSH connection...${NC}"
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$DEPLOYMENT_USER@$SERVER_IP" "echo 'SSH connection successful'" 2>/dev/null; then
        echo -e "${GREEN}✅ SSH connection successful${NC}"
    else
        echo -e "${RED}❌ SSH connection failed${NC}"
        echo "Please ensure:"
        echo "  1. SSH key is set up for $DEPLOYMENT_USER@$SERVER_IP"
        echo "  2. Server is accessible from your network"
        echo "  3. SSH service is running on the server"
        exit 1
    fi
}

# Setup server environment
setup_server() {
    echo -e "${BLUE}🔧 Setting up server environment...${NC}"
    
    # Create setup script
    cat > /tmp/server_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "🐧 Updating system packages..."
apt-get update -y
apt-get upgrade -y

echo "📦 Installing required packages..."
apt-get install -y \
    docker.io \
    docker-compose \
    git \
    curl \
    wget \
    unzip \
    htop \
    ncdu \
    fail2ban \
    ufw \
    python3 \
    python3-pip

echo "🐳 Starting Docker service..."
systemctl start docker
systemctl enable docker

# Add user to docker group if not root
if [[ "$USER" != "root" ]]; then
    usermod -aG docker $USER
fi

echo "🔥 Setting up UFW firewall..."
# Allow SSH
ufw allow 22

# Allow HTTP/HTTPS 
ufw allow 80
ufw allow 443

# Allow trading system ports
ufw allow 8000:8010/tcp  # Main services
ufw allow 11434/tcp     # Ollama

# Enable firewall
echo "y" | ufw enable

echo "🛡️ Configuring fail2ban..."
systemctl start fail2ban
systemctl enable fail2ban

echo "📁 Creating application directories..."
mkdir -p /opt/ai-trading-system
mkdir -p /opt/ai-trading-system/logs
mkdir -p /opt/ai-trading-system/database
mkdir -p /opt/ai-trading-system/backups

# Set ownership
chown -R $USER:$USER /opt/ai-trading-system

echo "✅ Server setup complete!"
EOF
    
    # Upload and run setup script
    scp /tmp/server_setup.sh "$DEPLOYMENT_USER@$SERVER_IP:/tmp/"
    ssh "$DEPLOYMENT_USER@$SERVER_IP" "chmod +x /tmp/server_setup.sh && /tmp/server_setup.sh"
    
    echo -e "${GREEN}✅ Server environment setup complete${NC}"
}

# Install Ollama on server
install_ollama() {
    echo -e "${BLUE}🤖 Installing Ollama for AI models...${NC}"
    
    cat > /tmp/ollama_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "📥 Downloading Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

echo "🚀 Starting Ollama service..."
systemctl start ollama
systemctl enable ollama

# Wait for Ollama to start
sleep 10

echo "📦 Pulling required AI models..."
ollama pull mistral
ollama pull phi3

echo "✅ Ollama setup complete!"
EOF
    
    scp /tmp/ollama_setup.sh "$DEPLOYMENT_USER@$SERVER_IP:/tmp/"
    ssh "$DEPLOYMENT_USER@$SERVER_IP" "chmod +x /tmp/ollama_setup.sh && /tmp/ollama_setup.sh"
    
    echo -e "${GREEN}✅ Ollama installation complete${NC}"
}

# Deploy application
deploy_application() {
    echo -e "${BLUE}📤 Deploying application to server...${NC}"
    
    # Create deployment package
    echo -e "${YELLOW}📦 Creating deployment package...${NC}"
    
    # Exclude unnecessary files
    cat > /tmp/.rsync-exclude << EOF
.git/
.vscode/
.claude/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
test_results/
test_data/
logs/*.log
*.tmp
.env.test
.DS_Store
EOF
    
    # Sync files to server
    rsync -avz --delete \
        --exclude-from=/tmp/.rsync-exclude \
        ./ "$DEPLOYMENT_USER@$SERVER_IP:$REMOTE_PATH/"
    
    # Create production environment file
    echo -e "${YELLOW}⚙️ Creating production environment configuration...${NC}"
    
    cat > /tmp/.env.production << EOF
# AI Trading System - Production Environment

# System Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DB_PATH=/opt/ai-trading-system/database/paper_trading.db

# Trading Configuration
TRADING_SYMBOL=BTCUSDT
STARTING_BALANCE=10000
TRADE_INTERVAL=30
TRADING_MODE=paper
TRADING_STRATEGY=RSI

# Service URLs (internal Docker network)
ORCHESTRATOR_URL=http://orchestrator:8000
PORTFOLIO_SERVICE_URL=http://portfolio-service:8001
RISK_MANAGER_URL=http://risk-manager:8002
ANALYST_AGENT_URL=http://market-news-analyst:8003
NOTIFICATION_SERVICE_URL=http://notification-service:8004
TRADE_EXECUTOR_URL=http://trade-executor:8005
PARAMETER_OPTIMIZER_URL=http://parameter-optimizer:8006

# AI Configuration
OLLAMA_URL=http://host.docker.internal:11434

# External APIs (configure these)
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_TRADING_ALERTS_CHANNEL=trading-alerts
SLACK_GENERAL_CHANNEL=general

NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# Risk Management
LOSS_THRESHOLD=0.05
MIN_TRADES_FOR_OPTIMIZATION=10
OPTIMIZATION_LOOKBACK_HOURS=24

# System Intervals (seconds)
ORCHESTRATION_INTERVAL=60
ANALYSIS_INTERVAL=300
MODE_SWITCH_INTERVAL=600
EOF
    
    # Upload environment file
    scp /tmp/.env.production "$DEPLOYMENT_USER@$SERVER_IP:$REMOTE_PATH/.env"
    
    echo -e "${GREEN}✅ Application deployment complete${NC}"
}

# Start services
start_services() {
    echo -e "${BLUE}🚀 Starting AI trading system services...${NC}"
    
    ssh "$DEPLOYMENT_USER@$SERVER_IP" << 'EOF'
cd /opt/ai-trading-system

echo "🐳 Starting services with Docker Compose..."
docker-compose -f docker-compose.agents.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service health..."
curl -s http://localhost:8000/health || echo "Orchestrator not ready yet"
curl -s http://localhost:8001/health || echo "Portfolio service not ready yet"

echo "✅ Services startup initiated"
EOF
    
    echo -e "${GREEN}✅ Services started successfully${NC}"
}

# Check deployment status
check_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    ssh "$DEPLOYMENT_USER@$SERVER_IP" << 'EOF'
cd /opt/ai-trading-system

echo "🐳 Docker container status:"
docker-compose -f docker-compose.agents.yml ps

echo ""
echo "🔍 Service health checks:"
echo "Orchestrator: $(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' || echo 'Not responding')"
echo "Portfolio: $(curl -s http://localhost:8001/health | grep -o '"status":"[^"]*"' || echo 'Not responding')"
echo "Risk Manager: $(curl -s http://localhost:8002/health | grep -o '"status":"[^"]*"' || echo 'Not responding')"
echo "Market Analyst: $(curl -s http://localhost:8003/health | grep -o '"status":"[^"]*"' || echo 'Not responding')"
echo "Notification: $(curl -s http://localhost:8004/health | grep -o '"status":"[^"]*"' || echo 'Not responding')"

echo ""
echo "💾 System resources:"
df -h /
free -h

echo ""
echo "📈 System load:"
uptime
EOF
}

# View logs
view_logs() {
    local service="${1:-orchestrator}"
    
    echo -e "${BLUE}📋 Viewing logs for $service...${NC}"
    
    ssh "$DEPLOYMENT_USER@$SERVER_IP" << EOF
cd /opt/ai-trading-system
docker-compose -f docker-compose.agents.yml logs -f --tail=50 $service
EOF
}

# Stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping AI trading system services...${NC}"
    
    ssh "$DEPLOYMENT_USER@$SERVER_IP" << 'EOF'
cd /opt/ai-trading-system

echo "🐳 Stopping Docker services..."
docker-compose -f docker-compose.agents.yml down

echo "✅ Services stopped"
EOF
    
    echo -e "${GREEN}✅ Services stopped successfully${NC}"
}

# Backup database and config
backup_system() {
    echo -e "${BLUE}💾 Creating system backup...${NC}"
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    
    ssh "$DEPLOYMENT_USER@$SERVER_IP" << EOF
cd /opt/ai-trading-system

echo "📦 Creating backup: $backup_name"
mkdir -p backups/$backup_name

# Backup database
cp -r database/ backups/$backup_name/

# Backup configuration
cp .env backups/$backup_name/
cp -r config/ backups/$backup_name/

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} backups/$backup_name/ \;

echo "🗜️ Compressing backup..."
cd backups
tar -czf $backup_name.tar.gz $backup_name/
rm -rf $backup_name/

echo "✅ Backup created: backups/$backup_name.tar.gz"
ls -lah $backup_name.tar.gz
EOF
    
    echo -e "${GREEN}✅ Backup completed${NC}"
}

# Main deployment function
main() {
    local command="${1:-help}"
    
    if [[ "$command" == "help" ]] || [[ -z "$command" ]]; then
        show_usage
        exit 0
    fi
    
    validate_inputs
    test_ssh_connection
    
    case $command in
        "setup")
            echo -e "${CYAN}🔧 Setting up Hetzner server environment...${NC}"
            setup_server
            install_ollama
            echo -e "${GREEN}✅ Server setup complete! Run 'deploy' next.${NC}"
            ;;
        "deploy")
            echo -e "${CYAN}🚀 Deploying AI trading system...${NC}"
            deploy_application
            start_services
            echo -e "${GREEN}✅ Deployment complete!${NC}"
            check_status
            ;;
        "update")
            echo -e "${CYAN}🔄 Updating deployment...${NC}"
            stop_services
            deploy_application
            start_services
            echo -e "${GREEN}✅ Update complete!${NC}"
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "status")
            check_status
            ;;
        "logs")
            view_logs "$2"
            ;;
        "backup")
            backup_system
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Cleanup on exit
cleanup() {
    rm -f /tmp/server_setup.sh
    rm -f /tmp/ollama_setup.sh
    rm -f /tmp/.env.production
    rm -f /tmp/.rsync-exclude
}

trap cleanup EXIT

# Run main function
main "$@"