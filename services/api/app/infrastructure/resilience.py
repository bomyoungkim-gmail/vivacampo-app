"""
Resiliency utilities: circuit breaker, retry with backoff, graceful shutdown.
"""
from functools import wraps
from typing import Callable, Any
import time
import asyncio
from datetime import datetime, timedelta, timezone
import structlog

logger = structlog.get_logger()


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by failing fast when error threshold is reached.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", func=func.__name__)
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", func=func.__name__)
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now(timezone.utc) - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Increment failure count and open circuit if threshold reached"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("circuit_breaker_opened", 
                          failure_count=self.failure_count,
                          threshold=self.failure_threshold)


def circuit(failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    Decorator for circuit breaker pattern.
    
    Usage:
        @circuit(failure_threshold=5, recovery_timeout=60)
        async def fetch_external_api():
            ...
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        return wrapper
    
    return decorator


def circuit_sync(failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    Sync decorator for circuit breaker pattern.
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper

    return decorator


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry with exponential backoff.
    
    Usage:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        async def upload_to_s3(file):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error("retry_exhausted",
                                   func=func.__name__,
                                   attempts=attempt,
                                   exc_info=e)
                        raise
                    
                    logger.warning("retry_attempt",
                                 func=func.__name__,
                                 attempt=attempt,
                                 delay=delay,
                                 error=str(e))
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
        
        return wrapper
    
    return decorator


def retry_with_backoff_sync(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Sync decorator for retry with exponential backoff.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            "retry_exhausted",
                            func=func.__name__,
                            attempts=attempt,
                            exc_info=e,
                        )
                        raise

                    logger.warning(
                        "retry_attempt",
                        func=func.__name__,
                        attempt=attempt,
                        delay=delay,
                        error=str(e),
                    )
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

        return wrapper

    return decorator


class GracefulShutdown:
    """
    Graceful shutdown handler for worker processes.
    Allows in-flight requests to complete before shutdown.
    """
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_tasks = set()
    
    def register_task(self, task):
        """Register an active task"""
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()
    
    def trigger_shutdown(self):
        """Trigger graceful shutdown"""
        logger.info("graceful_shutdown_triggered", active_tasks=len(self.active_tasks))
        self.shutdown_event.set()
    
    async def wait_for_tasks(self, timeout: int = 30):
        """Wait for active tasks to complete"""
        if not self.active_tasks:
            return
        
        logger.info("waiting_for_tasks", count=len(self.active_tasks))
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks, return_exceptions=True),
                timeout=timeout
            )
            logger.info("all_tasks_completed")
        
        except asyncio.TimeoutError:
            logger.warning("shutdown_timeout", remaining_tasks=len(self.active_tasks))


# Global shutdown handler
shutdown_handler = GracefulShutdown()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    import signal
    
    def handle_signal(signum, frame):
        logger.info("shutdown_signal_received", signal=signum)
        shutdown_handler.trigger_shutdown()
    
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
