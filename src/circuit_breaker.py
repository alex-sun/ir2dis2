#!/usr/bin/env python3

"""
Circuit Breaker implementation for the iRacing Discord Bot.
Prevents repeated API calls to failing services and provides fallback behavior.
"""

import time
from typing import Optional, Callable, Any, Awaitable
from src.logging_config import get_logger

logger = get_logger(__name__)

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    
    States:
    - CLOSED: Normal operation - allow calls
    - OPEN: Service is considered unhealthy - reject calls immediately
    - HALF-OPEN: Testing if service has recovered - allow limited calls
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds to wait before transitioning to half-open
            half_open_max_calls: Max number of calls allowed in half-open state
            name: Identifier for logging purposes
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # State variables
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = self.State.CLOSED
        self.half_open_call_count = 0
        
        # Add correlation ID to all logs from this circuit breaker
        from src.logging_config import add_correlation_id
        add_correlation_id(logger, f"cb-{name}")
        
        logger.info(f"Circuit breaker '{name}' initialized with failure_threshold={failure_threshold}, recovery_timeout={recovery_timeout}s")

    class State:
        """Circuit breaker states"""
        CLOSED = "CLOSED"
        OPEN = "OPEN"
        HALF_OPEN = "HALF_OPEN"

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.half_open_call_count = 0
        logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED state")

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = self.State.OPEN
        self.last_failure_time = time.time()
        logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN state (failures: {self.failure_count}/{self.failure_threshold})")

    def _transition_to_half_open(self):
        """Transition to HALF-OPEN state"""
        self.state = self.State.HALF_OPEN
        self.half_open_call_count = 0
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF-OPEN state")

    def _record_failure(self):
        """Record a failure and update circuit breaker state"""
        self.failure_count += 1
        
        if self.state == self.State.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
        elif self.state == self.State.HALF_OPEN:
            self._transition_to_open()

    def _record_success(self):
        """Record a success and update circuit breaker state"""
        if self.state == self.State.HALF_OPEN:
            self.half_open_call_count += 1
            
            if self.half_open_call_count >= self.half_open_max_calls:
                self._transition_to_closed()
        elif self.state == self.State.OPEN:
            # Success in OPEN state doesn't change state immediately
            pass
        # No state change needed in CLOSED state

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by the function
        """
        # Check if we should allow the call based on current state
        if self.state == self.State.OPEN:
            time_since_last_failure = time.time() - self.last_failure_time
            
            if time_since_last_failure < self.recovery_timeout:
                # Still in recovery period
                wait_time = self.recovery_timeout - time_since_last_failure
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. Try again in {wait_time:.1f}s. "
                    f"Failed {self.failure_count} times in the last {self.recovery_timeout}s."
                )
            else:
                # Recovery timeout expired - transition to half-open
                self._transition_to_half_open()

        if self.state == self.State.HALF_OPEN:
            if self.half_open_call_count >= self.half_open_max_calls:
                # Too many concurrent calls in half-open state
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is in HALF-OPEN state but has reached max concurrent calls ({self.half_open_max_calls})"
                )

        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            return result

        except Exception as e:
            # Record failure
            self._record_failure()
            
            # Re-raise the original exception
            raise e

    async def call_async(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """
        Execute an asynchronous function with circuit breaker protection.
        
        Args:
            func: Asynchronous function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the asynchronous function call
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by the function
        """
        # Check if we should allow the call based on current state
        if self.state == self.State.OPEN:
            time_since_last_failure = time.time() - self.last_failure_time
            
            if time_since_last_failure < self.recovery_timeout:
                # Still in recovery period
                wait_time = self.recovery_timeout - time_since_last_failure
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. Try again in {wait_time:.1f}s. "
                    f"Failed {self.failure_count} times in the last {self.recovery_timeout}s."
                )
            else:
                # Recovery timeout expired - transition to half-open
                self._transition_to_half_open()

        if self.state == self.State.HALF_OPEN:
            if self.half_open_call_count >= self.half_open_max_calls:
                # Too many concurrent calls in half-open state
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is in HALF-OPEN state but has reached max concurrent calls ({self.half_open_max_calls})"
                )

        try:
            # Execute the asynchronous function
            result = await func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            return result

        except Exception as e:
            # Record failure
            self._record_failure()
            
            # Re-raise the original exception
            raise e

    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        self._transition_to_closed()
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")

# Global circuit breakers for API services
iracing_api_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    half_open_max_calls=1,
    name="iracing-api"
)

discord_api_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    half_open_max_calls=1,
    name="discord-api"
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=10,
    recovery_timeout=120.0,
    half_open_max_calls=2,
    name="database"
)