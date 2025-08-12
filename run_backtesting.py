#!/usr/bin/env python3
"""
Script to run backtesting and optimization for the AI Trading System
"""

import os
import sys
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting_engine import AdvancedBacktestingEngine
from src.parameter_optimizer_service import ParameterOptimizer

def run_backtesting():
    """Run backtesting with the AdvancedBacktestingEngine"""
    print("🚀 Starting backtesting...")
    
    # Create backtesting engine
    backtester = AdvancedBacktestingEngine()
    
    # Run comprehensive backtest
    results = backtester.run_comprehensive_backtest(
        symbol="BTC-USD",
        initial_balance=10000,
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Backtesting completed. Results saved to {results_file}")
    return results

def run_optimization():
    """Run parameter optimization"""
    print("🔧 Starting parameter optimization...")
    
    # Create parameter optimizer
    optimizer = ParameterOptimizer()
    
    # Run optimization
    optimization_results = optimizer.run_optimization()
    
    # Save optimization results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    opt_results_file = f"optimization_results_{timestamp}.json"
    
    with open(opt_results_file, 'w') as f:
        json.dump(optimization_results, f, indent=2)
    
    print(f"✅ Parameter optimization completed. Results saved to {opt_results_file}")
    return optimization_results

def main():
    """Main function to run backtesting and optimization"""
    print("🤖 AI Trading System - Backtesting and Optimization")
    print("=" * 50)
    
    # Run backtesting
    backtest_results = run_backtesting()
    
    # Run optimization
    optimization_results = run_optimization()
    
    print("\n🎉 All processes completed successfully!")
    
    # Print summary
    print("\n📊 Summary:")
    print(f"  Backtest results saved to: backtest_results_*.json")
    print(f"  Optimization results saved to: optimization_results_*.json")

if __name__ == "__main__":
    main()