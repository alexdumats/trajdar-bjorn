#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation
Prevents cascade failures by temporarily blocking requests to failing services
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Type
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failures detected, requests blocked
    HALF_OPEN = "HALF_OPEN" # Testing recovery with limited requests

class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors"""
    pass

class CircuitOpenError(CircuitBreakerError):
    """Exception raised when circuit is open"""
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        expected_exceptions: tuple = (Exception,),
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_duration: Time in seconds to wait before half-open state
            expected_exceptions: Tuple of exceptions that count as failures
            name: Name for logging purposes
        """
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.expected_exceptions = expected_exceptions
        self.name = name
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_success_count = 0
        
        logger.info(f"🔧 Circuit breaker '{name}' initialized: threshold={failure_threshold}, timeout={timeout_duration}s")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator interface"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception raised by the function
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                logger.warning(f"🚫 Circuit breaker '{self.name}' is OPEN, blocking request to {func.__name__}")
                raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exception, still count as failure for circuit breaker
            self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout_duration
    
    def _set_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_success_count = 0
        logger.info(f"🔄 Circuit breaker '{self.name}' transitioning to HALF_OPEN")
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_success_count += 1
            # If we've had enough successful calls, close the circuit
            if self.half_open_success_count >= 2:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
                logger.info(f"✅ Circuit breaker '{self.name}' failure count reset")
    
    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"⚠️ Circuit breaker '{self.name}' failure #{self.failure_count}: {exception}")
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state sends us back to open
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        logger.error(f"💥 Circuit breaker '{self.name}' OPENED after {self.failure_count} failures")
    
    def _close_circuit(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_success_count = 0
        logger.info(f"✅ Circuit breaker '{self.name}' CLOSED -恢复正常")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "timeout_duration": self.timeout_duration,
            "last_failure_time": self.last_failure_time,
            "time_since_last_failure": time.time() - self.last_failure_time if self.last_failure_time else None
        }

# Pre-configured circuit breakers for common services
binance_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout_duration=30,
    expected_exceptions=(ConnectionError, TimeoutError, Exception),
    name="BinanceAPI"
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout_duration=60,
    expected_exceptions=(ConnectionError, Exception),
    name="Database"
)

if __name__ == "__main__":
    # Example usage
    import requests
    from requests.exceptions import RequestException, Timeout
    
    # Create a circuit breaker for an external API
    api_breaker = CircuitBreaker(
        failure_threshold=3,
        timeout_duration=30,
        expected_exceptions=(RequestException, Timeout),
        name="ExternalAPI"
    )
    
    @api_breaker
    def fetch_data():
        """Simulate API call"""
        # Simulate random failures
        import random
        if random.random() < 0.7:  # 70% failure rate for demo
            raise RequestException("API temporarily unavailable")
        return {"data": "success"}
    
    # Test the circuit breaker
    for i in range(10):
        try:
            result = fetch_data()
            print(f"Call {i+1}: Success - {result}")
        except CircuitOpenError:
            print(f"Call {i+1}: Circuit OPEN - Request blocked")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
        
        print(f"State: {api_breaker.get_state()}")
        time.sleep(1)