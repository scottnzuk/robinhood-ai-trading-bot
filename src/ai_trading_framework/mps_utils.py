import asyncio
import functools
import time
import traceback
import torch
import logging

device = "mps" if torch.backends.mps.is_built() else "cpu"

def safe_mps_op(fn):
    """
    Decorator to fallback to CPU if MPS op fails.
    Supports both sync and async functions.
    """
    @functools.wraps(fn)
    def sync_wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except RuntimeError as e:
            if "MPS" in str(e):
                logging.warning(f"MPS op failed: {e}. Falling back to CPU.")
                args = [a.to("cpu") if isinstance(a, torch.Tensor) and getattr(a, 'device', None) and a.device.type == "mps" else a for a in args]
                kwargs = {k: (v.to("cpu") if isinstance(v, torch.Tensor) and getattr(v, 'device', None) and v.device.type == "mps" else v) for k,v in kwargs.items()}
                return fn(*args, **kwargs)
            else:
                raise

    @functools.wraps(fn)
    async def async_wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except RuntimeError as e:
            if "MPS" in str(e):
                logging.warning(f"(async) MPS op failed: {e}. Falling back to CPU.")
                args = [a.to("cpu") if isinstance(a, torch.Tensor) and getattr(a, 'device', None) and a.device.type == "mps" else a for a in args]
                kwargs = {k: (v.to("cpu") if isinstance(v, torch.Tensor) and getattr(v, 'device', None) and v.device.type == "mps" else v) for k,v in kwargs.items()}
                return await fn(*args, **kwargs)
            else:
                raise

    if asyncio.iscoroutinefunction(fn):
        return async_wrapper
    else:
        return sync_wrapper

def timeout_async(timeout_sec):
    """
    Decorator to timeout async functions.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
            except asyncio.TimeoutError:
                logging.error(f"TIMEOUT: Function '{func.__name__}' timed out after {timeout_sec}s")
                traceback.print_stack()
                return None
        return wrapper
    return decorator

class Watchdog:
    """
    Async watchdog manager for monitoring coroutines.
    """
    def __init__(self, timeout_sec=30):
        self.timeout_sec = timeout_sec
        self.tasks = []

    def watch(self, coro, name="task"):
        async def monitored():
            try:
                return await asyncio.wait_for(coro, timeout=self.timeout_sec)
            except asyncio.TimeoutError:
                logging.error(f"WATCHDOG: {name} timed out after {self.timeout_sec}s")
                traceback.print_stack()
                return None
        task = asyncio.create_task(monitored())
        self.tasks.append(task)
        return task

    async def wait_all(self):
        return await asyncio.gather(*self.tasks, return_exceptions=True)

def log_diagnostic(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[DIAGNOSTIC] {timestamp} - {message}")