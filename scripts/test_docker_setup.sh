#!/bin/bash

# AI Trading System - Docker Test Environment Setup
# Sets up containerized test environment for integration testing

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${CYAN}🐳 AI Trading System - Docker Test Environment${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"

# Create test-specific docker-compose file
create_test_compose() {
    echo -e "${BLUE}📝 Creating test docker-compose configuration...${NC}"
    
    cat > "$PROJECT_ROOT/docker-compose.test.yml" << 'EOF'
version: '3.8'

services:
  # Test Database
  test-database:
    image: sqlite:latest
    container_name: test-trading-database
    volumes:
      - ./test_data:/data
    networks:
      - test-network

  # Portfolio Service (Test Mode)
  test-portfolio-service:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-portfolio-service
    ports:
      - "8001:8001"
    environment:
      - SERVICE_PORT=8001
      - DB_PATH=/app/test_data/test.db
      - TESTING=true
      - PYTHONPATH=/app
    volumes:
      - ./test_data:/app/test_data
      - ./logs:/app/logs
    depends_on:
      - test-database
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Risk Manager Service (Test Mode)  
  test-risk-manager:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-risk-manager
    ports:
      - "8002:8002"
    environment:
      - SERVICE_PORT=8002
      - TESTING=true
      - MOCK_OLLAMA=true
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
      - ./test_config:/app/test_config
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Market Analyst Service (Test Mode)
  test-market-analyst:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-market-analyst
    ports:
      - "8003:8003"
    environment:
      - SERVICE_PORT=8003
      - TESTING=true
      - MOCK_EXTERNAL_APIS=true
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
      - ./test_config:/app/test_config
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Notification Service (Test Mode)
  test-notification:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-notification
    ports:
      - "8004:8004"
    environment:
      - SERVICE_PORT=8004
      - TESTING=true
      - DISABLE_SLACK=true
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Orchestrator Service (Test Mode)
  test-orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-orchestrator
    ports:
      - "8000:8000"
    environment:
      - SERVICE_PORT=8000
      - PORTFOLIO_SERVICE_URL=http://test-portfolio-service:8001
      - RISK_MANAGER_URL=http://test-risk-manager:8002
      - ANALYST_AGENT_URL=http://test-market-analyst:8003
      - NOTIFICATION_SERVICE_URL=http://test-notification:8004
      - TESTING=true
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
      - ./test_config:/app/test_config
    depends_on:
      - test-portfolio-service
      - test-risk-manager
      - test-market-analyst
      - test-notification
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Test Runner Container
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: test-runner
    environment:
      - TESTING=true
      - PYTEST_ARGS=${PYTEST_ARGS:-tests/}
      - PYTHONPATH=/app
    volumes:
      - .:/app
      - ./test_results:/app/test_results
    depends_on:
      - test-orchestrator
    networks:
      - test-network
    command: ["pytest", "${PYTEST_ARGS:-tests/}", "-v", "--tb=short"]

networks:
  test-network:
    driver: bridge
EOF
    
    echo -e "${GREEN}✅ Test docker-compose configuration created${NC}"
}

# Create test Dockerfile
create_test_dockerfile() {
    echo -e "${BLUE}🐳 Creating test Dockerfile...${NC}"
    
    cat > "$PROJECT_ROOT/Dockerfile.test" << 'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-mock \
    pytest-html \
    pytest-cov \
    pytest-xdist \
    pytest-profiling

# Copy application code
COPY src/ src/
COPY tests/ tests/
COPY scripts/ scripts/
COPY config/ config/
COPY pytest.ini .

# Create necessary directories
RUN mkdir -p /app/test_data /app/test_results /app/logs

# Set environment variables for testing
ENV TESTING=true
ENV PYTHONPATH=/app
ENV LOG_LEVEL=WARNING

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT:-8000}/health || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "pytest", "tests/", "-v"]
EOF
    
    echo -e "${GREEN}✅ Test Dockerfile created${NC}"
}

# Start test environment
start_test_environment() {
    echo -e "${BLUE}🚀 Starting test environment...${NC}"
    
    # Build test images
    echo -e "${YELLOW}Building test images...${NC}"
    docker-compose -f docker-compose.test.yml build --no-cache
    
    # Start services
    echo -e "${YELLOW}Starting test services...${NC}"
    docker-compose -f docker-compose.test.yml up -d --remove-orphans
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    
    local services=("test-portfolio-service" "test-risk-manager" "test-market-analyst" "test-notification" "test-orchestrator")
    local max_attempts=30
    local attempt=0
    
    for service in "${services[@]}"; do
        while [[ $attempt -lt $max_attempts ]]; do
            if docker-compose -f docker-compose.test.yml ps --format json | jq -r '.[] | select(.Name=="'$service'") | .Health' | grep -q "healthy"; then
                echo -e "${GREEN}✅ $service is healthy${NC}"
                break
            else
                echo -e "${YELLOW}⏳ Waiting for $service to be healthy... (attempt $((attempt + 1))/$max_attempts)${NC}"
                sleep 5
                ((attempt++))
            fi
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            echo -e "${RED}❌ $service failed to become healthy${NC}"
            docker-compose -f docker-compose.test.yml logs $service
            exit 1
        fi
        
        attempt=0
    done
    
    echo -e "${GREEN}✅ All test services are healthy${NC}"
}

# Run integration tests in Docker
run_docker_tests() {
    local test_type="${1:-integration}"
    
    echo -e "${BLUE}🧪 Running $test_type tests in Docker...${NC}"
    
    case $test_type in
        "integration")
            PYTEST_ARGS="tests/integration/ -v --tb=short"
            ;;
        "e2e")
            PYTEST_ARGS="tests/e2e/ -v --tb=short"
            ;;
        "all")
            PYTEST_ARGS="tests/ -v --tb=short --durations=10"
            ;;
        *)
            PYTEST_ARGS="tests/$test_type/ -v --tb=short"
            ;;
    esac
    
    # Run tests in container
    docker-compose -f docker-compose.test.yml run --rm \
        -e PYTEST_ARGS="$PYTEST_ARGS" \
        test-runner
    
    local test_result=$?
    
    if [[ $test_result -eq 0 ]]; then
        echo -e "${GREEN}✅ Docker tests completed successfully${NC}"
    else
        echo -e "${RED}❌ Docker tests failed${NC}"
        echo -e "${YELLOW}📋 Checking service logs...${NC}"
        docker-compose -f docker-compose.test.yml logs --tail=50
    fi
    
    return $test_result
}

# Stop test environment
stop_test_environment() {
    echo -e "${BLUE}🛑 Stopping test environment...${NC}"
    
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
    
    # Clean up test images (optional)
    if [[ "$1" == "--clean-images" ]]; then
        echo -e "${YELLOW}🧹 Cleaning up test images...${NC}"
        docker images --filter="dangling=true" -q | xargs -r docker rmi
    fi
    
    echo -e "${GREEN}✅ Test environment stopped${NC}"
}

# Show test environment status
show_test_status() {
    echo -e "${BLUE}📊 Test Environment Status${NC}"
    echo -e "${BLUE}═════════════════════════${NC}"
    
    if docker-compose -f docker-compose.test.yml ps --format table; then
        echo ""
        echo -e "${CYAN}🔗 Service URLs:${NC}"
        echo -e "  • Orchestrator: http://localhost:8000/health"
        echo -e "  • Portfolio:    http://localhost:8001/health" 
        echo -e "  • Risk Manager: http://localhost:8002/health"
        echo -e "  • Market Analyst: http://localhost:8003/health"
        echo -e "  • Notification: http://localhost:8004/health"
    else
        echo -e "${RED}❌ Test environment is not running${NC}"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup          Set up test environment"
    echo "  start          Start test services"
    echo "  stop           Stop test services"
    echo "  test [TYPE]    Run tests (integration, e2e, all)"
    echo "  status         Show environment status"
    echo "  logs [SERVICE] Show service logs"
    echo "  clean          Clean up environment and images"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 test integration"
    echo "  $0 stop --clean-images"
}

# Main function
main() {
    local command="${1:-help}"
    
    case $command in
        "setup")
            create_test_compose
            create_test_dockerfile
            echo -e "${GREEN}✅ Docker test environment setup complete${NC}"
            echo -e "${CYAN}Next: Run '$0 start' to start the test environment${NC}"
            ;;
        "start")
            start_test_environment
            show_test_status
            ;;
        "stop")
            stop_test_environment "$2"
            ;;
        "test")
            run_docker_tests "$2"
            ;;
        "status")
            show_test_status
            ;;
        "logs")
            if [[ -n "$2" ]]; then
                docker-compose -f docker-compose.test.yml logs -f "$2"
            else
                docker-compose -f docker-compose.test.yml logs -f
            fi
            ;;
        "clean")
            stop_test_environment --clean-images
            rm -f docker-compose.test.yml Dockerfile.test
            echo -e "${GREEN}✅ Test environment cleaned${NC}"
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"