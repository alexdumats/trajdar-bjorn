#!/bin/bash
# Start Refactored Trading System
# Launches all services in the correct order with proper dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.refactored.yml"
ENV_FILE=".env"
LOG_DIR="logs"
PID_DIR="pids"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️ $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# Function to check if required files exist
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.production.template" ]; then
            cp .env.production.template .env
            print_warning "Please edit .env file with your actual values before continuing."
            print_warning "Required variables: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_AUTHORIZED_USERS"
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error ".env file and template not found. Please create .env file with required variables."
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR" "$PID_DIR"
    
    print_success "Prerequisites check completed"
}

# Function to validate environment variables
validate_environment() {
    print_status "Validating environment variables..."
    
    # Source the .env file
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Check required Slack variables
    if [ -z "$SLACK_BOT_TOKEN" ]; then
        print_error "SLACK_BOT_TOKEN is not set in .env file"
        exit 1
    fi
    
    if [ -z "$SLACK_APP_TOKEN" ]; then
        print_warning "SLACK_APP_TOKEN is not set. Some features may not work."
    fi
    
    if [ -z "$SLACK_AUTHORIZED_USERS" ]; then
        print_warning "SLACK_AUTHORIZED_USERS is not set. Parameter updates will be disabled."
    fi
    
    print_success "Environment validation completed"
}

# Function to pull and prepare Ollama models
prepare_ollama_models() {
    print_status "Preparing Ollama models..."
    
    # Start Ollama service first
    docker-compose -f "$COMPOSE_FILE" up -d ollama
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    sleep 10
    
    # Pull required models
    print_status "Pulling mistral7b:latest model..."
    docker exec ollama-runtime ollama pull mistral7b:latest || {
        print_warning "Failed to pull mistral7b:latest, trying mistral:latest..."
        docker exec ollama-runtime ollama pull mistral:latest
    }
    
    print_status "Pulling phi3 model..."
    docker exec ollama-runtime ollama pull phi3 || {
        print_warning "Failed to pull phi3 model. Trade executor may use fallback."
    }
    
    print_success "Ollama models prepared"
}

# Function to start core infrastructure
start_infrastructure() {
    print_status "Starting core infrastructure..."
    
    # Start database and Ollama
    docker-compose -f "$COMPOSE_FILE" up -d database ollama
    
    # Wait for services to be ready
    sleep 5
    
    print_success "Core infrastructure started"
}

# Function to start Slack integration
start_slack_integration() {
    print_status "Starting Slack integration service..."
    
    docker-compose -f "$COMPOSE_FILE" up -d slack-integration
    
    # Wait for Slack integration to be ready
    sleep 10
    
    # Check if Slack integration is healthy
    if curl -f http://localhost:8009/health >/dev/null 2>&1; then
        print_success "Slack integration service started successfully"
    else
        print_warning "Slack integration service may not be fully ready"
    fi
}

# Function to start AI agents
start_agents() {
    print_status "Starting AI agents..."
    
    # Start agents in dependency order
    print_status "Starting Market Analyst..."
    docker-compose -f "$COMPOSE_FILE" up -d market-analyst
    sleep 5
    
    print_status "Starting News Analyst..."
    docker-compose -f "$COMPOSE_FILE" up -d news-analyst
    sleep 5
    
    print_status "Starting Risk Manager..."
    docker-compose -f "$COMPOSE_FILE" up -d risk-manager
    sleep 5
    
    print_status "Starting Trade Executor..."
    docker-compose -f "$COMPOSE_FILE" up -d trade-executor
    sleep 5
    
    print_status "Starting Parameter Optimizer..."
    docker-compose -f "$COMPOSE_FILE" up -d parameter-optimizer
    sleep 5
    
    print_success "AI agents started"
}

# Function to start scheduling and orchestration
start_orchestration() {
    print_status "Starting orchestration services..."
    
    # Start enhanced scheduler
    print_status "Starting Enhanced Mutual Scheduler..."
    docker-compose -f "$COMPOSE_FILE" up -d enhanced-scheduler
    sleep 5
    
    # Start supporting services
    print_status "Starting supporting services..."
    docker-compose -f "$COMPOSE_FILE" up -d portfolio-service notification-service
    sleep 5
    
    # Start main orchestrator
    print_status "Starting Main Orchestrator..."
    docker-compose -f "$COMPOSE_FILE" up -d orchestrator
    sleep 5
    
    print_success "Orchestration services started"
}

# Function to check system health
check_system_health() {
    print_status "Checking system health..."
    
    # Define services and their health endpoints
    declare -A services=(
        ["Slack Integration"]="http://localhost:8009/health"
        ["Market Analyst"]="http://localhost:8007/health"
        ["News Analyst"]="http://localhost:8008/health"
        ["Risk Manager"]="http://localhost:8002/health"
        ["Trade Executor"]="http://localhost:8005/health"
        ["Parameter Optimizer"]="http://localhost:8006/health"
        ["Enhanced Scheduler"]="http://localhost:8010/health"
        ["Portfolio Service"]="http://localhost:8001/health"
        ["Notification Service"]="http://localhost:8004/health"
        ["Main Orchestrator"]="http://localhost:8000/health"
    )
    
    healthy_count=0
    total_count=${#services[@]}
    
    for service in "${!services[@]}"; do
        endpoint="${services[$service]}"
        if curl -f "$endpoint" >/dev/null 2>&1; then
            print_success "$service is healthy"
            ((healthy_count++))
        else
            print_warning "$service is not responding"
        fi
    done
    
    print_status "System Health: $healthy_count/$total_count services healthy"
    
    if [ $healthy_count -eq $total_count ]; then
        print_success "All services are healthy!"
        return 0
    else
        print_warning "Some services are not healthy. Check logs for details."
        return 1
    fi
}

# Function to show system status
show_system_status() {
    print_status "System Status:"
    echo ""
    
    # Show running containers
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_status "Service Endpoints:"
    echo "  • Main Orchestrator: http://localhost:8000"
    echo "  • Market Analyst: http://localhost:8007"
    echo "  • News Analyst: http://localhost:8008"
    echo "  • Slack Integration: http://localhost:8009"
    echo "  • Enhanced Scheduler: http://localhost:8010"
    echo "  • Risk Manager: http://localhost:8002"
    echo "  • Trade Executor: http://localhost:8005"
    echo "  • Parameter Optimizer: http://localhost:8006"
    echo "  • Portfolio Service: http://localhost:8001"
    echo "  • Notification Service: http://localhost:8004"
    echo "  • Ollama: http://localhost:11434"
    
    echo ""
    print_status "Management Commands:"
    echo "  • Start orchestration: curl -X POST http://localhost:8000/start-orchestration"
    echo "  • Stop orchestration: curl -X POST http://localhost:8000/stop-orchestration"
    echo "  • System status: curl http://localhost:8000/system-status"
    echo "  • Scheduler status: curl http://localhost:8010/status"
    
    echo ""
    print_status "Slack Channels:"
    echo "  • #market-analyst - Market analysis updates"
    echo "  • #news-analyst - News sentiment updates"
    echo "  • #risk-manager - Risk assessment alerts"
    echo "  • #trade-executor - Trade execution notifications"
    echo "  • #parameter-optimizer - Optimization updates"
    echo "  • #orchestrator - System coordination messages"
    echo "  • #trading-alerts - Critical alerts"
    echo "  • #system-health - System health reports"
}

# Function to start orchestration
start_trading_orchestration() {
    print_status "Starting trading orchestration..."
    
    # Start orchestration via API
    if curl -X POST http://localhost:8000/start-orchestration >/dev/null 2>&1; then
        print_success "Trading orchestration started successfully"
    else
        print_error "Failed to start trading orchestration"
        return 1
    fi
    
    # Start enhanced scheduler
    if curl -X POST http://localhost:8010/start-scheduler >/dev/null 2>&1; then
        print_success "Enhanced scheduler started successfully"
    else
        print_warning "Enhanced scheduler may already be running"
    fi
}

# Main execution
main() {
    echo "🚀 Starting Refactored AI Trading System"
    echo "========================================"
    
    # Run all startup steps
    check_prerequisites
    validate_environment
    start_infrastructure
    prepare_ollama_models
    start_slack_integration
    start_agents
    start_orchestration
    
    # Wait for all services to stabilize
    print_status "Waiting for services to stabilize..."
    sleep 15
    
    # Check system health
    if check_system_health; then
        print_success "System startup completed successfully!"
        
        # Start trading orchestration
        start_trading_orchestration
        
        # Show system status
        show_system_status
        
        echo ""
        print_success "🎉 Refactored AI Trading System is now running!"
        print_status "Monitor logs with: docker-compose -f $COMPOSE_FILE logs -f"
        print_status "Stop system with: docker-compose -f $COMPOSE_FILE down"
        
    else
        print_error "System startup completed with issues. Check service logs."
        echo ""
        print_status "Check logs with: docker-compose -f $COMPOSE_FILE logs [service-name]"
        exit 1
    fi
}

# Handle script arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "health")
        check_system_health
        ;;
    "status")
        show_system_status
        ;;
    "orchestration")
        start_trading_orchestration
        ;;
    *)
        echo "Usage: $0 [start|health|status|orchestration]"
        echo "  start        - Start the complete system (default)"
        echo "  health       - Check system health"
        echo "  status       - Show system status"
        echo "  orchestration - Start trading orchestration"
        exit 1
        ;;
esac