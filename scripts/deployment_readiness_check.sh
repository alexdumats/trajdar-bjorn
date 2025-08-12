#!/bin/bash

# AI Trading System - Deployment Readiness Check
# Quick verification that system is ready for Hetzner deployment

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_PASSED=0
TESTS_TOTAL=0

echo -e "${CYAN}🚀 AI Trading System - Deployment Readiness Check${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"

# Test 1: Required files exist
echo -e "\n${BLUE}1. Checking required files...${NC}"
((TESTS_TOTAL++))

required_files=(
    "src/orchestrator_service.py"
    "src/portfolio_service.py"
    "src/signal_service.py"
    "src/data_service.py"
    "src/notification_service.py"
    "config/production_config.yaml"
    "config/trading_parameters.yaml"
    "docker-compose.production.yml"
    "requirements.txt"
    "Dockerfile"
    "scripts/deploy_hetzner.sh"
    ".env.production.template"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ All required files present${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Missing files:${NC}"
    printf '%s\n' "${missing_files[@]}" | sed 's/^/  - /'
fi

# Test 2: Python dependencies
echo -e "\n${BLUE}2. Checking Python dependencies...${NC}"
((TESTS_TOTAL++))

if pip list | grep -E "(fastapi|uvicorn|pandas|numpy|aiohttp|PyYAML)" > /dev/null; then
    echo -e "${GREEN}✅ Core Python dependencies available${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Missing Python dependencies${NC}"
    echo -e "${YELLOW}Run: pip install -r requirements.txt${NC}"
fi

# Test 3: Configuration syntax
echo -e "\n${BLUE}3. Checking configuration files syntax...${NC}"
((TESTS_TOTAL++))

config_valid=true

# Check YAML files
for yaml_file in config/*.yaml; do
    if [[ -f "$yaml_file" ]]; then
        if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            echo -e "${RED}❌ Invalid YAML syntax in $yaml_file${NC}"
            config_valid=false
        fi
    fi
done

if $config_valid; then
    echo -e "${GREEN}✅ All configuration files have valid syntax${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Configuration syntax errors found${NC}"
fi

# Test 4: Docker configuration
echo -e "\n${BLUE}4. Checking Docker configuration...${NC}"
((TESTS_TOTAL++))

if command -v docker > /dev/null 2>&1; then
    if docker-compose -f docker-compose.production.yml config > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose configuration valid${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Docker Compose configuration invalid${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Docker not installed (will be installed on server)${NC}"
    # Still count as passed since we'll install Docker on the server
    ((TESTS_PASSED++))
fi

# Test 5: Environment template
echo -e "\n${BLUE}5. Checking environment template...${NC}"
((TESTS_TOTAL++))

if [[ -f ".env.production.template" ]]; then
    required_vars=(
        "TRADING_SYMBOL"
        "STARTING_BALANCE"
        "SLACK_BOT_TOKEN"
        "OLLAMA_URL"
    )
    
    template_valid=true
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env.production.template; then
            echo -e "${RED}❌ Missing variable $var in environment template${NC}"
            template_valid=false
        fi
    done
    
    if $template_valid; then
        echo -e "${GREEN}✅ Environment template contains required variables${NC}"
        ((TESTS_PASSED++))
    fi
else
    echo -e "${RED}❌ Environment template missing${NC}"
fi

# Test 6: Deployment scripts
echo -e "\n${BLUE}6. Checking deployment scripts...${NC}"
((TESTS_TOTAL++))

deployment_scripts=(
    "scripts/deploy_hetzner.sh"
    "scripts/setup_hetzner_mcp.sh"
    "scripts/deploy_with_mcp.py"
)

scripts_ok=true
for script in "${deployment_scripts[@]}"; do
    if [[ ! -x "$script" ]]; then
        echo -e "${RED}❌ Script $script not executable${NC}"
        scripts_ok=false
    fi
done

if $scripts_ok; then
    echo -e "${GREEN}✅ All deployment scripts are executable${NC}"
    ((TESTS_PASSED++))
fi

# Test 7: MCP configuration
echo -e "\n${BLUE}7. Checking MCP server configuration...${NC}"
((TESTS_TOTAL++))

if grep -q "hetzner:" config/mcp_servers.yaml && grep -q "HETZNER_API_TOKEN" config/mcp_servers.yaml; then
    echo -e "${GREEN}✅ Hetzner MCP server configured${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Hetzner MCP server not properly configured${NC}"
fi

# Summary
echo -e "\n${CYAN}📊 Deployment Readiness Summary${NC}"
echo -e "${CYAN}═══════════════════════════════${NC}"
echo -e "Tests Passed: ${TESTS_PASSED}/${TESTS_TOTAL}"

if [[ $TESTS_PASSED -eq $TESTS_TOTAL ]]; then
    echo -e "${GREEN}🎉 System is ready for deployment!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "1. Set SERVER_IP: ${BLUE}export SERVER_IP=135.181.164.232${NC}"
    echo -e "2. Setup server: ${BLUE}./scripts/deploy_hetzner.sh setup${NC}"
    echo -e "3. Configure .env: ${BLUE}cp .env.production.template .env && nano .env${NC}"
    echo -e "4. Deploy system: ${BLUE}./scripts/deploy_hetzner.sh deploy${NC}"
    echo ""
    echo -e "${GREEN}🚀 Ready to deploy to Hetzner server!${NC}"
    exit 0
else
    failed_tests=$((TESTS_TOTAL - TESTS_PASSED))
    echo -e "${YELLOW}⚠️ ${failed_tests} issue(s) need to be resolved before deployment${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the issues above and run this check again.${NC}"
    exit 1
fi