#!/bin/bash

# AI Trading System - Test Runner Script
# Comprehensive test execution with reporting and environment setup

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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_RESULTS_DIR="$PROJECT_ROOT/test_results"
LOG_DIR="$PROJECT_ROOT/logs"

# Create necessary directories
mkdir -p "$TEST_RESULTS_DIR" "$LOG_DIR"

echo -e "${CYAN}🧪 AI Trading System - Test Suite Runner${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"

# Function to show usage
show_usage() {
    echo "Usage: $0 [TEST_TYPE] [OPTIONS]"
    echo ""
    echo "Test Types:"
    echo "  unit          Run unit tests only"
    echo "  integration   Run integration tests only"  
    echo "  e2e           Run end-to-end tests only"
    echo "  performance   Run performance tests only"
    echo "  stress        Run stress tests only"
    echo "  all           Run all tests (default)"
    echo ""
    echo "Options:"
    echo "  --coverage    Generate coverage report"
    echo "  --html        Generate HTML report"
    echo "  --verbose     Verbose output"
    echo "  --parallel    Run tests in parallel"
    echo "  --fail-fast   Stop on first failure"
    echo "  --no-cov      Skip coverage collection"
    echo "  --junit       Generate JUnit XML report"
    echo "  --profile     Profile test execution"
    echo ""
    echo "Examples:"
    echo "  $0 unit --coverage"
    echo "  $0 all --html --verbose"
    echo "  $0 performance --junit"
}

# Parse command line arguments
TEST_TYPE="${1:-all}"
shift 2>/dev/null || true

COVERAGE=false
HTML_REPORT=false
VERBOSE=false
PARALLEL=false
FAIL_FAST=false
NO_COV=false
JUNIT_XML=false
PROFILE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --no-cov)
            NO_COV=true
            shift
            ;;
        --junit)
            JUNIT_XML=true
            shift
            ;;
        --profile)
            PROFILE=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Validate test type
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|e2e|performance|stress|all)$ ]]; then
    echo -e "${RED}❌ Invalid test type: $TEST_TYPE${NC}"
    show_usage
    exit 1
fi

# Environment setup
setup_test_environment() {
    echo -e "${BLUE}🔧 Setting up test environment...${NC}"
    
    # Set environment variables for testing
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export TESTING=true
    export DB_PATH="$PROJECT_ROOT/test_results/test.db"
    export LOG_LEVEL=WARNING
    export DISABLE_NOTIFICATIONS=true
    export MOCK_EXTERNAL_APIS=true
    
    # Create test database directory
    mkdir -p "$(dirname "$DB_PATH")"
    
    echo -e "${GREEN}✅ Test environment configured${NC}"
}

# Check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}❌ pytest not found. Installing...${NC}"
        pip install pytest pytest-asyncio pytest-mock pytest-html
    fi
    
    # Check for optional dependencies
    if $COVERAGE && ! python -c "import pytest_cov" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Installing pytest-cov for coverage reporting...${NC}"
        pip install pytest-cov
    fi
    
    if $PARALLEL && ! python -c "import pytest_xdist" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Installing pytest-xdist for parallel execution...${NC}"
        pip install pytest-xdist
    fi
    
    if $PROFILE && ! python -c "import pytest_profiling" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Installing pytest-profiling...${NC}"
        pip install pytest-profiling
    fi
    
    echo -e "${GREEN}✅ Dependencies verified${NC}"
}

# Build pytest command
build_pytest_command() {
    local cmd="pytest"
    
    # Add test path based on type
    case $TEST_TYPE in
        unit)
            cmd="$cmd tests/unit/"
            ;;
        integration)
            cmd="$cmd tests/integration/"
            ;;
        e2e)
            cmd="$cmd tests/e2e/"
            ;;
        performance)
            cmd="$cmd tests/performance/ -m performance"
            ;;
        stress)
            cmd="$cmd tests/performance/ -m stress"
            ;;
        all)
            cmd="$cmd tests/"
            ;;
    esac
    
    # Add markers for specific test types
    if [[ "$TEST_TYPE" == "performance" ]]; then
        cmd="$cmd -m 'performance and not stress'"
    elif [[ "$TEST_TYPE" == "stress" ]]; then
        cmd="$cmd -m stress"
    fi
    
    # Add options
    if $VERBOSE; then
        cmd="$cmd -v --tb=long"
    fi
    
    if $FAIL_FAST; then
        cmd="$cmd -x"
    fi
    
    if $PARALLEL; then
        # Use number of CPU cores
        cmd="$cmd -n auto"
    fi
    
    # Coverage options
    if $COVERAGE && ! $NO_COV; then
        cmd="$cmd --cov=src --cov-report=term-missing"
        
        if $HTML_REPORT; then
            cmd="$cmd --cov-report=html:$TEST_RESULTS_DIR/htmlcov"
        fi
    fi
    
    # HTML report
    if $HTML_REPORT; then
        cmd="$cmd --html=$TEST_RESULTS_DIR/report.html --self-contained-html"
    fi
    
    # JUnit XML
    if $JUNIT_XML; then
        cmd="$cmd --junit-xml=$TEST_RESULTS_DIR/junit.xml"
    fi
    
    # Profiling
    if $PROFILE; then
        cmd="$cmd --profile --profile-svg"
    fi
    
    # Additional options
    cmd="$cmd --durations=10"
    cmd="$cmd --strict-markers"
    cmd="$cmd --color=yes"
    
    echo "$cmd"
}

# Run specific test suite
run_tests() {
    local test_type=$1
    local start_time=$(date +%s)
    
    echo -e "${CYAN}🚀 Running $test_type tests...${NC}"
    
    # Build and execute pytest command
    local pytest_cmd=$(build_pytest_command)
    echo -e "${BLUE}Command: $pytest_cmd${NC}"
    echo ""
    
    # Execute tests
    if eval "$pytest_cmd" 2>&1 | tee "$TEST_RESULTS_DIR/${test_type}_output.log"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo ""
        echo -e "${GREEN}✅ $test_type tests completed successfully in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo ""
        echo -e "${RED}❌ $test_type tests failed after ${duration}s${NC}"
        return 1
    fi
}

# Generate test summary
generate_summary() {
    echo -e "${CYAN}📊 Test Summary${NC}"
    echo -e "${CYAN}═══════════════${NC}"
    
    if [[ -f "$TEST_RESULTS_DIR/junit.xml" ]]; then
        echo -e "${BLUE}JUnit XML report: $TEST_RESULTS_DIR/junit.xml${NC}"
    fi
    
    if [[ -d "$TEST_RESULTS_DIR/htmlcov" ]]; then
        echo -e "${BLUE}Coverage HTML report: $TEST_RESULTS_DIR/htmlcov/index.html${NC}"
    fi
    
    if [[ -f "$TEST_RESULTS_DIR/report.html" ]]; then
        echo -e "${BLUE}Test HTML report: $TEST_RESULTS_DIR/report.html${NC}"
    fi
    
    # Show test result files
    if ls "$TEST_RESULTS_DIR"/*.log &> /dev/null; then
        echo -e "${BLUE}Test logs:${NC}"
        ls -la "$TEST_RESULTS_DIR"/*.log
    fi
    
    echo ""
    echo -e "${PURPLE}💡 Test Results Directory: $TEST_RESULTS_DIR${NC}"
}

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Remove temporary test files if any
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Keep test results but clean old temporary files
    find "$TEST_RESULTS_DIR" -name "*.tmp" -delete 2>/dev/null || true
}

# Main execution
main() {
    # Handle interruptions
    trap cleanup SIGINT SIGTERM
    
    # Setup
    setup_test_environment
    check_dependencies
    
    echo ""
    echo -e "${CYAN}🎯 Test Configuration:${NC}"
    echo -e "  Test Type: $TEST_TYPE"
    echo -e "  Coverage: $COVERAGE"
    echo -e "  HTML Report: $HTML_REPORT"
    echo -e "  Parallel: $PARALLEL"
    echo -e "  Verbose: $VERBOSE"
    echo ""
    
    # Run tests
    if run_tests "$TEST_TYPE"; then
        echo ""
        generate_summary
        echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
        exit 0
    else
        echo ""
        generate_summary
        echo -e "${RED}💥 Test execution failed!${NC}"
        exit 1
    fi
}

# Run main function
main "$@"