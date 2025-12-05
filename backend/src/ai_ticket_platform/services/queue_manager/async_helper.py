"""Async helper utilities for RQ workers.

This module provides utilities for running async code in synchronous RQ worker contexts.
Event loops are automatically cleaned up when the process exits to prevent resource leaks.
"""

import asyncio
import atexit
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-local storage for persistent event loop in RQ workers
_thread_local = threading.local()


def _cleanup_event_loop(loop):
	"""Clean up a single event loop safely."""
	if loop is None or loop.is_closed():
		return

	try:
		# Cancel all pending tasks
		pending = asyncio.all_tasks(loop)
		for task in pending:
			task.cancel()

		# Run loop once more to process cancellations
		if pending:
			loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

		loop.close()
		logger.debug("[_cleanup_event_loop] Event loop closed successfully")
	except Exception as e:
		logger.error(f"[_cleanup_event_loop] Error during cleanup: {str(e)}")


def _cleanup_on_exit():
	"""Clean up the current thread's event loop on process exit."""
	if hasattr(_thread_local, 'loop'):
		_cleanup_event_loop(_thread_local.loop)
		_thread_local.loop = None


# Register cleanup handler for process exit
atexit.register(_cleanup_on_exit)


def _get_or_create_event_loop():
	"""Get or create a persistent event loop for the current thread.

	This avoids the issue of asyncio.run() closing the loop while
	database connections are still using it.
	"""
	if not hasattr(_thread_local, 'loop') or _thread_local.loop is None or _thread_local.loop.is_closed():
		_thread_local.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(_thread_local.loop)
		logger.debug("[_get_or_create_event_loop] Created new persistent event loop")
	return _thread_local.loop


def _run_async(coro):
	"""Helper to run async code in sync context (for RQ workers).

	Uses a persistent event loop per thread to avoid connection issues
	when the loop is closed prematurely.
	"""
	loop = _get_or_create_event_loop()
	return loop.run_until_complete(coro)
