#!/usr/bin/env python3
"""
Centralized Configuration Manager for Trajdar Trading System
Loads and manages all trading parameters from centralized config files
NO MORE HARDCODED VALUES ANYWHERE!
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

class ConfigManager:
    """Centralized configuration management for the trading system"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
            
        # Initialize Sentry if configuration is available
        sentry_config = self.get_sentry_config()
        if sentry_config.get('dsn') and sentry_config['dsn'] != "https://examplePublicKey@o0.ingest.sentry.io/0":
            self._init_sentry(sentry_config)
    
    def load_config(self):
        """Load configuration from YAML files"""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            
            # Load main trading parameters
            trading_config_path = project_root / "config" / "trading_parameters.yaml"
            if trading_config_path.exists():
                with open(trading_config_path, 'r') as f:
                    content = f.read()
                    # Replace environment variables in the YAML content
                    content = self._substitute_env_vars(content)
                    self._config = yaml.safe_load(content)
                    logging.info(f"✅ Loaded trading config from {trading_config_path}")
            else:
                logging.error(f"❌ Trading config not found at {trading_config_path}")
                self._config = {}
            
            # Load additional production config if exists
            prod_config_path = project_root / "config" / "production_config.yaml"
            if prod_config_path.exists():
                with open(prod_config_path, 'r') as f:
                    prod_content = f.read()
                    prod_content = self._substitute_env_vars(prod_content)
                    prod_config = yaml.safe_load(prod_content)
                    
                    # Merge production config (trading_parameters takes precedence)
                    if prod_config:
                        self._merge_configs(prod_config, self._config)
                        logging.info(f"✅ Merged production config from {prod_config_path}")
                        
        except Exception as e:
            logging.error(f"❌ Failed to load configuration: {e}")
            self._config = {}
    
    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR:default} patterns with environment variables"""
        import re
        
        def replace_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default = var_expr.split(':', 1)
            else:
                var_name, default = var_expr, ''
            
            return os.getenv(var_name, default)
        
        # Replace ${VAR:default} patterns
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_var, content)
    
    def _merge_configs(self, source: dict, target: dict):
        """Merge source config into target config (target takes precedence)"""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                self._merge_configs(value, target[key])
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation path
        Example: get('rsi.period') or get('risk_management.max_position_size')
        """
        if not self._config:
            return default
            
        keys = path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_rsi_config(self) -> Dict[str, Any]:
        """Get RSI configuration"""
        return {
            'period': self.get('rsi.period', 14),
            'oversold_threshold': self.get('rsi.oversold_threshold', 30),
            'overbought_threshold': self.get('rsi.overbought_threshold', 70),
            'neutral_value': self.get('rsi.neutral_value', 50.0),
            'smoothing_factor': self.get('rsi.smoothing_factor', 1.0),
            'price_source': self.get('rsi.price_source', 'close')
        }
    
    def get_risk_management_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return {
            'max_position_size': self.get('risk_management.max_position_size', 0.1),
            'min_position_size': self.get('risk_management.min_position_size', 0.001),
            'stop_loss_pct': self.get('risk_management.stop_loss_pct', 0.05),
            'take_profit_pct': self.get('risk_management.take_profit_pct', 0.1),
            'max_daily_trades': self.get('risk_management.max_daily_trades', 50),
            'max_daily_loss': self.get('risk_management.max_daily_loss', 0.1),
            'min_usdc_balance': self.get('risk_management.min_usdc_balance', 100.0),
            'min_confidence': self.get('risk_management.min_confidence', 0.6)
        }
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration"""
        return {
            'trade_interval_seconds': self.get('execution.trade_interval_seconds', 30),
            'price_check_interval': self.get('execution.price_check_interval', 5),
            'price_history_limit': self.get('execution.price_history_limit', 50),
            'klines_limit': self.get('execution.klines_limit', 100),
            'api_timeout_seconds': self.get('execution.api_timeout_seconds', 30),
            'retry_attempts': self.get('execution.retry_attempts', 3),
            'retry_delay_seconds': self.get('execution.retry_delay_seconds', 1)
        }
    
    def get_signal_config(self) -> Dict[str, Any]:
        """Get signal generation configuration"""
        return {
            'sources': self.get('signals.sources', ['rsi', 'volume', 'price_action']),
            'require_multiple_confirmations': self.get('signals.require_multiple_confirmations', True),
            'min_signals_for_trade': self.get('signals.min_signals_for_trade', 1),
            'volume_min_ratio': self.get('signals.volume.min_volume_ratio', 1.5),
            'volume_ma_period': self.get('signals.volume.volume_ma_period', 20),
            'min_price_movement': self.get('signals.price_action.min_price_movement', 0.005),
            'trend_confirmation_periods': self.get('signals.price_action.trend_confirmation_periods', 3)
        }
    
    def get_markets_config(self) -> Dict[str, Any]:
        """Get markets configuration"""
        symbols_str = self.get('markets.symbols', 'BTCUSDC,ETHUSDC,SOLUSDC')
        if isinstance(symbols_str, str):
            symbols = [s.strip() for s in symbols_str.split(',')]
        else:
            symbols = symbols_str
            
        return {
            'symbols': symbols,
            'base_currency': self.get('markets.base_currency', 'USDC'),
            'min_liquidity': self.get('markets.min_liquidity', 1000000),
            'max_spread_pct': self.get('markets.max_spread_pct', 0.01)
        }
    
    def get_portfolio_config(self) -> Dict[str, Any]:
        """Get portfolio configuration"""
        return {
            'starting_balance': self.get('portfolio.starting_balance', 10000),
            'reserve_balance_pct': self.get('portfolio.reserve_balance_pct', 0.05),
            'max_positions': self.get('portfolio.max_positions', 5),
            'max_correlation': self.get('portfolio.max_correlation', 0.8),
            'rebalance_threshold': self.get('portfolio.rebalance_threshold', 0.1),
            'rebalance_frequency_hours': self.get('portfolio.rebalance_frequency_hours', 24)
        }
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get optimization configuration"""
        return {
            'enable_auto_optimization': self.get('optimization.enable_auto_optimization', True),
            'loss_threshold': self.get('optimization.optimization_triggers.loss_threshold', 0.05),
            'win_rate_threshold': self.get('optimization.optimization_triggers.win_rate_threshold', 0.4),
            'drawdown_threshold': self.get('optimization.optimization_triggers.drawdown_threshold', 0.05),
            'min_trades_for_stats': self.get('optimization.optimization_triggers.min_trades_for_stats', 10),
            'max_optimizations_per_day': self.get('optimization.max_optimizations_per_day', 3),
            'optimization_cooldown_hours': self.get('optimization.optimization_cooldown_hours', 6),
            'backtest_period_days': self.get('optimization.backtest_period_days', 365),
            'optimization_iterations': self.get('optimization.optimization_iterations', 100)
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return {
            'health_check_interval': self.get('monitoring.health_check_interval', 30),
            'service_timeout': self.get('monitoring.service_timeout', 60),
            'track_metrics': self.get('monitoring.track_metrics', ['total_return', 'win_rate']),
            'critical_loss_pct': self.get('monitoring.alerts.critical_loss_pct', 0.1),
            'low_win_rate': self.get('monitoring.alerts.low_win_rate', 0.3),
            'high_drawdown': self.get('monitoring.alerts.high_drawdown', 0.08),
            'service_down_minutes': self.get('monitoring.alerts.service_down_minutes', 5)
        }
        
    def get_sentry_config(self) -> Dict[str, Any]:
        """Get Sentry configuration"""
        return {
            'dsn': self.get('monitoring.sentry.dsn', os.getenv('SENTRY_DSN', '')),
            'environment': self.get('monitoring.sentry.environment', os.getenv('SENTRY_ENVIRONMENT', 'production')),
            'traces_sample_rate': float(self.get('monitoring.sentry.traces_sample_rate', os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.2))),
            'profiles_sample_rate': float(self.get('monitoring.sentry.profiles_sample_rate', os.getenv('SENTRY_PROFILES_SAMPLE_RATE', 0.1))),
            'debug': str(self.get('monitoring.sentry.debug', os.getenv('SENTRY_DEBUG', 'false'))).lower() == 'true',
            'release': self.get('monitoring.sentry.release', self.get('system.version', '1.0.0'))
        }
        
    def _init_sentry(self, config: Dict[str, Any]):
        """Initialize Sentry with the provided configuration"""
        try:
            # Set up logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            # Initialize Sentry SDK with performance monitoring
            sentry_sdk.init(
                dsn=config['dsn'],
                environment=config['environment'],
                traces_sample_rate=config['traces_sample_rate'],  # Enable performance monitoring
                profiles_sample_rate=config['profiles_sample_rate'],  # Enable profiling
                debug=config['debug'],
                release=config['release'],
                integrations=[
                    logging_integration,
                    sentry_sdk.integrations.threading.ThreadingIntegration(propagate_hub=True),
                ],
                # Configure performance
                _experiments={
                    "profiles_sample_rate": config['profiles_sample_rate'],
                },
                # Add default tags
                default_tags={
                    "app_name": self.get('system.name', 'AI Trading System'),
                    "trading_mode": self.get('trading.mode', 'paper'),
                    "trading_symbol": self.get('trading.symbol', 'BTCUSDC'),
                }
            )
            
            # Set tags for better filtering in Sentry
            sentry_sdk.set_tag("app_name", self.get('system.name', 'AI Trading System'))
            sentry_sdk.set_tag("trading_mode", self.get('trading.mode', 'paper'))
            
            logging.info(f"✅ Sentry initialized for environment: {config['environment']}")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Sentry: {e}")
    
    def get_optimization_bounds(self) -> Dict[str, Any]:
        """Get optimization bounds configuration"""
        return {
            'rsi': {
                'period_min': self.get('optimization.bounds.rsi.period_min', 5),
                'period_max': self.get('optimization.bounds.rsi.period_max', 21),
                'oversold_min': self.get('optimization.bounds.rsi.oversold_min', 20),
                'oversold_max': self.get('optimization.bounds.rsi.oversold_max', 35),
                'overbought_min': self.get('optimization.bounds.rsi.overbought_min', 65),
                'overbought_max': self.get('optimization.bounds.rsi.overbought_max', 85)
            },
            'risk_management': {
                'position_size_min': self.get('optimization.bounds.risk_management.position_size_min', 0.05),
                'position_size_max': self.get('optimization.bounds.risk_management.position_size_max', 0.25),
                'stop_loss_min': self.get('optimization.bounds.risk_management.stop_loss_min', 0.02),
                'stop_loss_max': self.get('optimization.bounds.risk_management.stop_loss_max', 0.05),
                'take_profit_min': self.get('optimization.bounds.risk_management.take_profit_min', 0.04),
                'take_profit_max': self.get('optimization.bounds.risk_management.take_profit_max', 0.10),
                'confidence_min': self.get('optimization.bounds.risk_management.confidence_min', 0.5),
                'confidence_max': self.get('optimization.bounds.risk_management.confidence_max', 0.8)
            }
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get general trading configuration"""
        return {
            'starting_balance': self.get('portfolio.starting_balance', 10000),
            'mode': self.get('trading.mode', 'paper'),
            'reserve_balance_pct': self.get('portfolio.reserve_balance_pct', 0.05),
            'max_positions': self.get('portfolio.max_positions', 5),
            'max_correlation': self.get('portfolio.max_correlation', 0.8)
        }
    
    def reload_config(self):
        """Reload configuration from files"""
        self.load_config()
        logging.info("🔄 Configuration reloaded")
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_paths = [
            'rsi.period',
            'rsi.oversold_threshold', 
            'rsi.overbought_threshold',
            'risk_management.max_position_size',
            'risk_management.stop_loss_pct',
            'risk_management.take_profit_pct',
            'execution.trade_interval_seconds'
        ]
        
        missing = []
        for path in required_paths:
            if self.get(path) is None:
                missing.append(path)
        
        if missing:
            logging.error(f"❌ Missing required configuration: {missing}")
            return False
        
        logging.info("✅ Configuration validation passed")
        return True


# Singleton instance
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get the singleton configuration instance"""
    return config


# Convenience functions for backward compatibility
def get_rsi_period() -> int:
    """Get RSI period"""
    return int(config.get('rsi.period', 14))


def get_rsi_thresholds() -> tuple:
    """Get RSI oversold and overbought thresholds"""
    return (
        int(config.get('rsi.oversold_threshold', 30)),
        int(config.get('rsi.overbought_threshold', 70))
    )


def get_risk_parameters() -> dict:
    """Get risk management parameters"""
    return config.get_risk_management_config()


if __name__ == "__main__":
    # Test the configuration manager
    print("🧪 Testing Configuration Manager")
    print("=" * 50)
    
    cfg = get_config()
    
    print(f"RSI Period: {cfg.get('rsi.period')}")
    print(f"RSI Thresholds: {get_rsi_thresholds()}")
    print(f"Max Position Size: {cfg.get('risk_management.max_position_size')}")
    print(f"Trading Symbols: {cfg.get('markets.symbols')}")
    
    print(f"\nValidation: {'✅ Passed' if cfg.validate_config() else '❌ Failed'}")
    
    print("\n🔧 RSI Config:")
    for k, v in cfg.get_rsi_config().items():
        print(f"  {k}: {v}")
    
    print("\n⚠️ Risk Management Config:")
    for k, v in cfg.get_risk_management_config().items():
        print(f"  {k}: {v}")