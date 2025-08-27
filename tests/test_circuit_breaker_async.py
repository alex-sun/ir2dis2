#!/usr/bin/env python3

"""
Tests for the Circuit Breaker async functionality.
"""

import asyncio
import unittest
from src.circuit_breaker import CircuitBreaker, CircuitBreakerError


class TestCircuitBreakerAsync(unittest.IsolatedAsyncioTestCase):
    async def test_call_async_basic_functionality(self):
        """Test basic functionality of call_async method"""
        
        # Create a circuit breaker with low thresholds for testing
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            half_open_max_calls=1,
            name="test-async"
        )
        
        # Successful async function
        async def successful_func():
            return "success"
        
        # Test successful call
        result = await cb.call_async(successful_func)
        self.assertEqual(result, "success")
        self.assertEqual(cb.state, cb.State.CLOSED)
        self.assertEqual(cb.failure_count, 0)

    async def test_call_async_failure_handling(self):
        """Test that call_async properly handles failures"""
        
        # Create a circuit breaker with low thresholds for testing
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            half_open_max_calls=1,
            name="test-async-failure"
        )
        
        # Failing async function
        async def failing_func():
            raise ValueError("Test failure")
        
        # First failure should not open circuit yet
        try:
            await cb.call_async(failing_func)
            self.fail("Should have raised an exception")
        except ValueError:
            pass  # Expected
        
        self.assertEqual(cb.state, cb.State.CLOSED)
        self.assertEqual(cb.failure_count, 1)
        
        # Second failure should open circuit
        try:
            await cb.call_async(failing_func)
            self.fail("Should have raised an exception")
        except ValueError:
            pass  # Expected
        
        self.assertEqual(cb.state, cb.State.OPEN)
        self.assertEqual(cb.failure_count, 2)

    async def test_call_async_circuit_breaker_error(self):
        """Test that call_async raises CircuitBreakerError when circuit is open"""
        
        # Create a circuit breaker with low thresholds for testing
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=2.0,
            half_open_max_calls=1,
            name="test-async-open"
        )
        
        # Failing async function
        async def failing_func():
            raise ValueError("Test failure")
        
        # Successful async function for this test
        async def successful_func():
            return "success"
        
        # Cause circuit to open
        try:
            await cb.call_async(failing_func)
            self.fail("Should have raised an exception")
        except ValueError:
            pass  # Expected
        
        self.assertEqual(cb.state, cb.State.OPEN)
        
        # Try to call when circuit is open - should get CircuitBreakerError
        try:
            await cb.call_async(successful_func)
            self.fail("Should have raised CircuitBreakerError")
        except CircuitBreakerError:
            pass  # Expected

    async def test_call_async_recovery(self):
        """Test that call_async allows recovery after timeout"""
        
        # Create a circuit breaker with low thresholds for testing
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1,  # Very short timeout for testing
            half_open_max_calls=1,
            name="test-async-recovery"
        )
        
        # Failing async function
        async def failing_func():
            raise ValueError("Test failure")
        
        # Successful async function
        async def successful_func():
            return "success"
        
        # Cause circuit to open
        try:
            await cb.call_async(failing_func)
            self.fail("Should have raised an exception")
        except ValueError:
            pass  # Expected
        
        self.assertEqual(cb.state, cb.State.OPEN)
        
        # Wait for recovery timeout to expire
        await asyncio.sleep(0.2)
        
        # Next call should transition to half-open
        try:
            result = await cb.call_async(successful_func)
            self.assertEqual(result, "success")
            self.assertEqual(cb.state, cb.State.CLOSED)  # Should transition back to closed after successful half-open call
        except Exception as e:
            self.fail(f"Should have succeeded: {e}")