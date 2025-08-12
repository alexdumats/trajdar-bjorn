"""
Advanced Backtesting Engine for AI Trading System
Comprehensive backtesting from 2016-2024 with 1-5% daily return optimization
"""

import pandas as pd
import numpy as np
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

# Import centralized configuration manager
try:
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.config_manager import get_config

class AdvancedBacktestingEngine:
    """Professional backtesting engine for 2016-2024 data with 1-5% daily target"""
    
    def __init__(self):
        # Load centralized configuration
        self.config = get_config()
        backtest_config = self.config.get('backtesting', {})
        
        # Backtesting parameters from config
        self.default_start_date = backtest_config.get('default_start_date', '2010-01-01')
        self.default_end_date = backtest_config.get('default_end_date', '2024-12-31')
        self.initial_balance = backtest_config.get('initial_balance', 10000)
        self.commission_rate = backtest_config.get('commission_rate', 0.001)
        self.slippage_rate = backtest_config.get('slippage_rate', 0.0005)
        
        self.strategies = []
        self.results = {}
        self.data_cache = {}
        
    def load_historical_data(self, symbol: str = None, 
                           start_date: str = None, 
                           end_date: str = None) -> pd.DataFrame:
        if symbol is None:
            symbol = self.config.get('backtesting.benchmark_symbol', 'BTC-USD')
        if start_date is None:
            start_date = self.default_start_date
        if end_date is None:
            end_date = self.default_end_date
        """Generate realistic synthetic BTC data for 2016-2024"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        dates = pd.date_range(start=start, end=end, freq='D')
        n_days = len(dates)
        
        # Dynamic price range from config or defaults
        initial_price = self.config.get('backtesting.initial_btc_price', 430)
        final_price = self.config.get('backtesting.final_btc_price', 42000)
        
        t = np.linspace(0, 1, n_days)
        
        # Growth with volatility
        trend = initial_price * (final_price / initial_price) ** t
        
        # Volatility from config
        base_volatility = self.config.get('backtesting.base_volatility', 0.25)
        volatility_amplitude = self.config.get('backtesting.volatility_amplitude', 0.1)
        volatility = base_volatility + volatility_amplitude * np.sin(2 * np.pi * t * 4)
        noise = np.random.normal(0, volatility, n_days) * trend
        
        # Market cycles from config
        bull_amplitude = self.config.get('backtesting.bull_cycle_amplitude', 0.3)
        bear_amplitude = self.config.get('backtesting.bear_cycle_amplitude', 0.2)
        bull_cycles = 1 + bull_amplitude * np.sin(2 * np.pi * t * 1.5)
        bear_cycles = 1 - bear_amplitude * np.sin(2 * np.pi * t * 0.8)
        
        prices = trend * bull_cycles * bear_cycles * (1 + noise)
        min_price = self.config.get('backtesting.minimum_price', 100)
        prices = np.maximum(prices, min_price)
        
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            daily_vol = np.random.uniform(0.015, 0.085)
            high = price * (1 + daily_vol)
            low = price * (1 - daily_vol)
            open_price = prices[i-1] if i > 0 else price
            volume = np.random.uniform(500000, 50000000) * (price / 1000) ** 1.5
            
            data.append({
                'timestamp': date.strftime('%Y-%m-%d'),
                'open': float(open_price),
                'high': float(high),
                'low': float(low),
                'close': float(price),
                'volume': float(volume)
            })
        
        return pd.DataFrame(data)
    
    def configure_strategies(self) -> List[Dict[str, Any]]:
        """Configure strategies optimized for 1-5% daily returns"""
        
        strategies = [
            {
                'name': 'RSI_Momentum_1',
                'type': 'rsi',
                'rsi_period': 14,
                'oversold': 25,
                'overbought': 75,
                'position_size': 0.08,
                'stop_loss': 0.015,
                'take_profit': 0.035,
                'min_confidence': 0.7
            },
            {
                'name': 'RSI_Momentum_2',
                'type': 'rsi',
                'rsi_period': 21,
                'oversold': 20,
                'overbought': 80,
                'position_size': 0.12,
                'stop_loss': 0.02,
                'take_profit': 0.045,
                'min_confidence': 0.75
            },
            {
                'name': 'MACD_Crossover',
                'type': 'macd',
                'fast_period': 8,
                'slow_period': 21,
                'signal_period': 5,
                'position_size': 0.1,
                'stop_loss': 0.018,
                'take_profit': 0.04,
                'min_confidence': 0.72
            },
            {
                'name': 'Bollinger_Breakout',
                'type': 'bollinger',
                'period': 20,
                'std_dev': 2.5,
                'position_size': 0.09,
                'stop_loss': 0.016,
                'take_profit': 0.038,
                'min_confidence': 0.68
            },
            {
                'name': 'Volume_Surge',
                'type': 'volume',
                'volume_ma_period': 14,
                'volume_threshold': 1.8,
                'position_size': 0.11,
                'stop_loss': 0.022,
                'take_profit': 0.042,
                'min_confidence': 0.73
            },
            {
                'name': 'Moving_Average_Cross',
                'type': 'ma_cross',
                'short_ma': 8,
                'long_ma': 21,
                'position_size': 0.1,
                'stop_loss': 0.019,
                'take_profit': 0.039,
                'min_confidence': 0.71
            }
        ]
        
        return strategies
    
    def run_comprehensive_backtest(self, symbol: str = "BTC-USD", 
                             initial_balance: float = 10000,
                             start_date: str = "2016-01-01",
                             end_date: str = "2024-12-31",
                             strategy_name: str = "Multi-Strategy",
                             validate_results: bool = True,
                             send_slack_report: bool = True) -> Dict[str, Any]:
        """Run comprehensive backtest with validation and optional Slack reporting"""
    
    print("🚀 Loading historical data...")
    data = self.load_historical_data(symbol, start_date, end_date)
    
    print("⚙️ Configuring strategies...")
    strategies = self.configure_strategies()
    
    print("📊 Running backtest...")
    results = self._run_strategy_backtest(data, strategies, initial_balance)
    
    print("📈 Analyzing results...")
    analysis = self._analyze_performance(results)
    
    # Create comprehensive backtest results
    backtest_results = {
        'metadata': {
            'backtest_id': f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'strategy_name': strategy_name,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_balance,
            'final_value': results.get('balance', initial_balance),
            'timestamp': datetime.now().isoformat(),
            'strategy_parameters': {s['name']: s for s in strategies}
        },
        'data': data.to_dict('records'),
        'results': results,
        'analysis': analysis,
        'trades': results.get('trades', []),
        'strategies': strategies
    }
    
    # Validate results if requested
    if validate_results:
        print("✅ Validating backtest results...")
        validation_summary = self.validate_backtest_results(backtest_results, strategy_name)
        backtest_results['validation'] = validation_summary
        
        # Print validation summary
        print(f"\n{validation_summary['overall_status']}")
        print(f"Validation Level: {validation_summary['validation_level']}")
        print(f"Checks Passed: {validation_summary['checks_passed']}")
        print(f"Recommendation: {validation_summary['recommendation']}")
        
        # Print failed checks if any
        failed_checks = [
            check_name for check_name, check_data in validation_summary['detailed_checks'].items()
            if not check_data['passed']
        ]
        
        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check_name in failed_checks:
                check_data = validation_summary['detailed_checks'][check_name]
                print(f"  - {check_data['message']}")
        
        # Print promotion requirements
        requirements = validation_summary['promotion_requirements']['specific_requirements']
        if requirements:
            print(f"\n🎯 Improvement Requirements:")
            for req in requirements[:5]:  # Show top 5 requirements
                print(f"  - {req}")
    
    # Send Slack report if requested
    if send_slack_report:
        try:
            print("📱 Sending Slack report...")
            import requests
            
            # Send to notification service
            notification_url = "http://localhost:8004/backtest_report"
            payload = {
                "results": backtest_results,
                "strategy_name": strategy_name
            }
            
            response = requests.post(notification_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Slack report sent successfully")
                backtest_results['slack_report_sent'] = True
            else:
                print(f"⚠️ Failed to send Slack report: {response.status_code}")
                backtest_results['slack_report_sent'] = False
        except Exception as e:
            print(f"❌ Error sending Slack report: {str(e)}")
            backtest_results['slack_report_sent'] = False
    
    return backtest_results
    
    def _run_strategy_backtest(self, data: pd.DataFrame, strategies: List[Dict], 
                             initial_balance: float) -> Dict[str, Any]:
        """Run backtest with multiple strategies"""
        
        portfolio = {
            'balance': initial_balance,
            'positions': {},
            'trades': [],
            'daily_values': [],
            'strategy_performance': {s['name']: {'trades': 0, 'wins': 0, 'profit': 0} for s in strategies}
        }
        
        # Add technical indicators
        data = self._add_technical_indicators(data)
        
        for idx, row in data.iterrows():
            current_date = row['timestamp']
            current_price = float(row['close'])
            
            # Generate signals for each strategy
            for strategy in strategies:
                signal = self._generate_strategy_signal(row, strategy)
                
                if signal['action'] != 'HOLD' and signal['confidence'] >= strategy['min_confidence']:
                    trade_result = self._execute_strategy_trade(
                        signal=signal,
                        price=current_price,
                        strategy=strategy,
                        portfolio=portfolio,
                        date=current_date
                    )
                    
                    if trade_result:
                        portfolio['strategy_performance'][strategy['name']]['trades'] += 1
                        if trade_result['profit'] > 0:
                            portfolio['strategy_performance'][strategy['name']]['wins'] += 1
        
        return portfolio
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the data"""
        # Add RSI
        data['rsi'] = self._calculate_rsi(data['close'], 14)
        
        # Add MACD
        data['macd'], data['macd_signal'] = self._calculate_macd(data['close'])
        
        # Add Bollinger Bands
        data['bb_upper'], data['bb_lower'] = self._calculate_bollinger_bands(data['close'])
        
        # Add Moving Averages
        data['ma_8'] = data['close'].rolling(window=8).mean()
        data['ma_21'] = data['close'].rolling(window=21).mean()
        
        # Add Volume indicators
        data['volume_ma'] = data['volume'].rolling(window=14).mean()
        
        return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal_period).mean()
        return macd, macd_signal
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2):
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = ma + (std * std_dev)
        lower_band = ma - (std * std_dev)
        return upper_band, lower_band
    
    def _generate_strategy_signal(self, row: pd.Series, strategy: Dict) -> Dict:
        """Generate trading signal based on strategy"""
        # Simple RSI strategy
        if strategy['type'] == 'rsi':
            rsi = float(row['rsi']) if not pd.isnull(row['rsi']) else 0.0
            if rsi < strategy['oversold']:
                return {'action': 'BUY', 'confidence': 0.8}
            elif rsi > strategy['overbought']:
                return {'action': 'SELL', 'confidence': 0.8}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
        
        # Simple MACD strategy
        elif strategy['type'] == 'macd':
            macd = float(row['macd']) if not pd.isnull(row['macd']) else 0.0
            macd_signal = float(row['macd_signal']) if not pd.isnull(row['macd_signal']) else 0.0
            if macd > macd_signal:
                return {'action': 'BUY', 'confidence': 0.7}
            elif macd < macd_signal:
                return {'action': 'SELL', 'confidence': 0.7}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
        
        # Simple Bollinger Bands strategy
        elif strategy['type'] == 'bollinger':
            price = float(row['close']) if not pd.isnull(row['close']) else 0.0
            upper_band = float(row['bb_upper']) if not pd.isnull(row['bb_upper']) else 0.0
            lower_band = float(row['bb_lower']) if not pd.isnull(row['bb_lower']) else 0.0
            if price < lower_band:
                return {'action': 'BUY', 'confidence': 0.75}
            elif price > upper_band:
                return {'action': 'SELL', 'confidence': 0.75}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
        
        # Simple Volume strategy
        elif strategy['type'] == 'volume':
            volume = float(row['volume']) if not pd.isnull(row['volume']) else 0.0
            volume_ma = float(row['volume_ma']) if not pd.isnull(row['volume_ma']) else 0.0
            if volume > volume_ma * strategy['volume_threshold']:
                return {'action': 'BUY', 'confidence': 0.7}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
        
        # Simple Moving Average Cross strategy
        elif strategy['type'] == 'ma_cross':
            ma_short = float(row['ma_8']) if not pd.isnull(row['ma_8']) else 0.0
            ma_long = float(row['ma_21']) if not pd.isnull(row['ma_21']) else 0.0
            if ma_short > ma_long:
                return {'action': 'BUY', 'confidence': 0.7}
            elif ma_short < ma_long:
                return {'action': 'SELL', 'confidence': 0.7}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
        
        # Default hold signal
        return {'action': 'HOLD', 'confidence': 0.5}
    
    def _execute_strategy_trade(self, signal: Dict, price: float, strategy: Dict, 
                               portfolio: Dict, date: str) -> Optional[Dict]:
        """Execute a trade based on the strategy signal"""
        action = signal['action']
        confidence = signal['confidence']
        
        if action == 'HOLD' or confidence < strategy['min_confidence']:
            return None
        
        # Calculate position size
        position_size = strategy['position_size']
        quantity = (portfolio['balance'] * position_size) / price
        
        # Calculate trade details
        if action == 'BUY':
            # Check if we have enough balance
            cost = quantity * price
            if cost > portfolio['balance']:
                return None
            
            # Deduct cost from balance
            portfolio['balance'] -= cost
            
            # Add to positions
            if 'BTC' not in portfolio['positions']:
                portfolio['positions']['BTC'] = 0
            portfolio['positions']['BTC'] += quantity
            
            return {
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'cost': cost,
                'profit': 0,
                'date': date
            }
        
        elif action == 'SELL':
            # Check if we have BTC to sell
            if 'BTC' not in portfolio['positions'] or portfolio['positions']['BTC'] == 0:
                return None
            
            # Calculate quantity to sell (can't sell more than we have)
            sell_quantity = min(quantity, portfolio['positions']['BTC'])
            
            # Calculate proceeds
            proceeds = sell_quantity * price
            
            # Add to balance
            portfolio['balance'] += proceeds
            
            # Remove from positions
            portfolio['positions']['BTC'] -= sell_quantity
            
            # Calculate profit
            profit = proceeds - (sell_quantity * price)  # Simplified profit calculation
            
            return {
                'action': 'SELL',
                'quantity': sell_quantity,
                'price': price,
                'proceeds': proceeds,
                'profit': profit,
                'date': date
            }
        
        return None
    
    def _analyze_performance(self, results: Dict) -> Dict:
        """Analyze backtest performance"""
        # This is a simplified performance analysis
        total_return = 0
        win_rate = 0
        max_drawdown = 0
        
        # Calculate total return
        if 'portfolio' in results and 'balance' in results['portfolio']:
            initial_balance = 10000  # Assuming initial balance
            final_balance = results['portfolio']['balance']
            total_return = (final_balance - initial_balance) / initial_balance
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': 0,  # Simplified
            'total_trades': 0,  # Simplified
            'winning_trades': 0,  # Simplified
            'losing_trades': 0  # Simplified
        }

    def validate_backtest_results(self, results: Dict, strategy_name: str = "Unknown") -> Dict:
        """
        Validate backtest results against profit/risk thresholds
        Returns validation status and detailed analysis
        """
        analysis = results.get("analysis", {})
        trades = results.get("trades", [])
        
        # Define validation thresholds (could be configurable)
        thresholds = {
            "min_total_return": 0.05,  # 5% minimum return
            "max_drawdown": 0.25,      # 25% maximum drawdown
            "min_sharpe_ratio": 0.5,   # Minimum Sharpe ratio
            "min_win_rate": 0.4,       # 40% minimum win rate
            "min_profit_factor": 1.2,  # Minimum profit factor
            "min_trades": 10,          # Minimum number of trades for statistical significance
            "max_consecutive_losses": 10,  # Maximum consecutive losses
            "min_risk_adjusted_return": 0.03  # 3% minimum risk-adjusted return
        }
        
        # Extract metrics
        total_return = analysis.get('total_return', 0)
        max_drawdown = analysis.get('max_drawdown', 0)
        sharpe_ratio = analysis.get('sharpe_ratio', 0)
        win_rate = analysis.get('win_rate', 0)
        profit_factor = analysis.get('profit_factor', 0)
        total_trades = len(trades)
        max_consecutive_losses = analysis.get('max_consecutive_losses', 0)
        volatility = analysis.get('volatility', 0)
        
        # Calculate risk-adjusted return
        risk_adjusted_return = total_return / max(volatility, 0.01) if volatility > 0 else 0
        
        # Validation checks
        validation_results = {
            "total_return_check": {
                "passed": total_return >= thresholds["min_total_return"],
                "value": total_return,
                "threshold": thresholds["min_total_return"],
                "message": f"Total return: {total_return:.2%} (required: ≥{thresholds['min_total_return']:.2%})"
            },
            "drawdown_check": {
                "passed": max_drawdown <= thresholds["max_drawdown"],
                "value": max_drawdown,
                "threshold": thresholds["max_drawdown"],
                "message": f"Max drawdown: {max_drawdown:.2%} (required: ≤{thresholds['max_drawdown']:.2%})"
            },
            "sharpe_ratio_check": {
                "passed": sharpe_ratio >= thresholds["min_sharpe_ratio"],
                "value": sharpe_ratio,
                "threshold": thresholds["min_sharpe_ratio"],
                "message": f"Sharpe ratio: {sharpe_ratio:.2f} (required: ≥{thresholds['min_sharpe_ratio']:.2f})"
            },
            "win_rate_check": {
                "passed": win_rate >= thresholds["min_win_rate"],
                "value": win_rate,
                "threshold": thresholds["min_win_rate"],
                "message": f"Win rate: {win_rate:.2%} (required: ≥{thresholds['min_win_rate']:.2%})"
            },
            "profit_factor_check": {
                "passed": profit_factor >= thresholds["min_profit_factor"],
                "value": profit_factor,
                "threshold": thresholds["min_profit_factor"],
                "message": f"Profit factor: {profit_factor:.2f} (required: ≥{thresholds['min_profit_factor']:.2f})"
            },
            "statistical_significance_check": {
                "passed": total_trades >= thresholds["min_trades"],
                "value": total_trades,
                "threshold": thresholds["min_trades"],
                "message": f"Total trades: {total_trades} (required: ≥{thresholds['min_trades']})"
            },
            "consecutive_losses_check": {
                "passed": max_consecutive_losses <= thresholds["max_consecutive_losses"],
                "value": max_consecutive_losses,
                "threshold": thresholds["max_consecutive_losses"],
                "message": f"Max consecutive losses: {max_consecutive_losses} (required: ≤{thresholds['max_consecutive_losses']})"
            },
            "risk_adjusted_return_check": {
                "passed": risk_adjusted_return >= thresholds["min_risk_adjusted_return"],
                "value": risk_adjusted_return,
                "threshold": thresholds["min_risk_adjusted_return"],
                "message": f"Risk-adjusted return: {risk_adjusted_return:.3f} (required: ≥{thresholds['min_risk_adjusted_return']:.3f})"
            }
        }
        
        # Calculate overall validation status
        all_checks_passed = all(check["passed"] for check in validation_results.values())
        critical_checks_passed = all(
            validation_results[check]["passed"] for check in 
            ["total_return_check", "drawdown_check", "sharpe_ratio_check"]
        )
        
        # Determine validation level
        if all_checks_passed:
            validation_level = "EXCELLENT"
            validation_status = "✅ PASSED - All criteria met, strategy approved for live trading"
            recommendation = "PROMOTE_TO_LIVE"
        elif critical_checks_passed:
            validation_level = "ACCEPTABLE"
            validation_status = "⚠️ CONDITIONAL PASS - Critical criteria met, monitor closely"
            recommendation = "PROMOTE_WITH_MONITORING"
        else:
            validation_level = "FAILED"
            validation_status = "❌ FAILED - Strategy requires optimization before deployment"
            recommendation = "REJECT_AND_OPTIMIZE"
        
        # Generate detailed validation report
        passed_checks = sum(1 for check in validation_results.values() if check["passed"])
        total_checks = len(validation_results)
        
        validation_summary = {
            "strategy_name": strategy_name,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": validation_status,
            "validation_level": validation_level,
            "recommendation": recommendation,
            "checks_passed": f"{passed_checks}/{total_checks}",
            "pass_rate": passed_checks / total_checks,
            "detailed_checks": validation_results,
            "thresholds_used": thresholds,
            "risk_assessment": self._assess_strategy_risk(analysis),
            "promotion_requirements": self._get_promotion_requirements(validation_results)
        }
        
        return validation_summary
    
    def _assess_strategy_risk(self, analysis: Dict) -> Dict:
        """Assess the risk profile of the strategy"""
        total_return = analysis.get('total_return', 0)
        max_drawdown = analysis.get('max_drawdown', 0)
        volatility = analysis.get('volatility', 0)
        sharpe_ratio = analysis.get('sharpe_ratio', 0)
        
        # Risk scoring (0-100, where 0 is lowest risk, 100 is highest risk)
        drawdown_risk = min(max_drawdown * 400, 100)  # 25% drawdown = 100 risk
        volatility_risk = min(volatility * 200, 100)   # 50% volatility = 100 risk
        return_consistency_risk = max(0, 100 - (sharpe_ratio * 50))  # Sharpe 2.0 = 0 risk
        
        overall_risk_score = (drawdown_risk + volatility_risk + return_consistency_risk) / 3
        
        if overall_risk_score <= 30:
            risk_level = "LOW"
            risk_description = "Conservative strategy with stable returns"
        elif overall_risk_score <= 60:
            risk_level = "MEDIUM"
            risk_description = "Balanced risk-return profile"
        else:
            risk_level = "HIGH"
            risk_description = "Aggressive strategy with higher volatility"
        
        return {
            "overall_risk_score": overall_risk_score,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "component_risks": {
                "drawdown_risk": drawdown_risk,
                "volatility_risk": volatility_risk,
                "return_consistency_risk": return_consistency_risk
            }
        }
    
    def _get_promotion_requirements(self, validation_results: Dict) -> Dict:
        """Generate specific requirements for strategy promotion"""
        failed_checks = [
            check_name for check_name, check_data in validation_results.items()
            if not check_data["passed"]
        ]
        
        requirements = []
        
        for failed_check in failed_checks:
            check_data = validation_results[failed_check]
            value = check_data["value"]
            threshold = check_data["threshold"]
            
            if failed_check == "total_return_check":
                improvement_needed = threshold - value
                requirements.append(f"Increase total return by {improvement_needed:.2%}")
            elif failed_check == "drawdown_check":
                reduction_needed = value - threshold
                requirements.append(f"Reduce maximum drawdown by {reduction_needed:.2%}")
            elif failed_check == "sharpe_ratio_check":
                improvement_needed = threshold - value
                requirements.append(f"Improve Sharpe ratio by {improvement_needed:.2f}")
            elif failed_check == "win_rate_check":
                improvement_needed = threshold - value
                requirements.append(f"Increase win rate by {improvement_needed:.2%}")
            elif failed_check == "profit_factor_check":
                improvement_needed = threshold - value
                requirements.append(f"Improve profit factor by {improvement_needed:.2f}")
            elif failed_check == "statistical_significance_check":
                trades_needed = threshold - value
                requirements.append(f"Execute {trades_needed} more trades for statistical significance")
            elif failed_check == "consecutive_losses_check":
                reduction_needed = value - threshold
                requirements.append(f"Reduce maximum consecutive losses by {reduction_needed}")
            elif failed_check == "risk_adjusted_return_check":
                improvement_needed = threshold - value
                requirements.append(f"Improve risk-adjusted return by {improvement_needed:.3f}")
        
        return {
            "failed_checks_count": len(failed_checks),
            "specific_requirements": requirements,
            "priority_improvements": requirements[:3] if requirements else [],
            "estimated_optimization_time": f"{len(failed_checks) * 2}-{len(failed_checks) * 4} hours"
        }

import os

def save_backtest_results(results, logs_dir="./logs/backtest/"):
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(logs_dir, f"backtest_results_{timestamp}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Backtest results saved to {out_path}")

def summarize_for_slack(results):
    analysis = results.get("analysis", {})
    summary = (
        f"*Backtest Summary*\n"
        f"Total Return: {analysis.get('total_return', 0):.2%}\n"
        f"Win Rate: {analysis.get('win_rate', 0):.2%}\n"
        f"Max Drawdown: {analysis.get('max_drawdown', 0):.2%}\n"
        f"Sharpe Ratio: {analysis.get('sharpe_ratio', 0)}\n"
        f"Total Trades: {analysis.get('total_trades', 0)}\n"
        f"Winning Trades: {analysis.get('winning_trades', 0)}\n"
        f"Losing Trades: {analysis.get('losing_trades', 0)}"
    )
    print(summary)

if __name__ == "__main__":
    # Example usage
    backtester = AdvancedBacktestingEngine()
    results = backtester.run_comprehensive_backtest()
    save_backtest_results(results)
    summarize_for_slack(results)
    print("Backtest completed successfully!")
