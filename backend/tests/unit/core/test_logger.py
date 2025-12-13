"""Unit tests for logger module."""

import pytest
import logging
from unittest.mock import MagicMock, patch

from ai_ticket_platform.core.logger.logger import (
	FileUploadFilter,
	Logger,
	add_context_to_log,
	LOG_CONTEXT,
)


class TestFileUploadFilter:
	"""Test FileUploadFilter redaction logic."""

	def test_filter_redacts_file_data(self):
		"""Test that file_data base64 content is redacted."""
		log_filter = FileUploadFilter()

		# Create a log record with file data
		record = logging.LogRecord(
			name="test",
			level=logging.INFO,
			pathname="test.py",
			lineno=1,
			msg="Request contains 'file_data': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...'",
			args=(),
			exc_info=None,
		)

		result = log_filter.filter(record)

		assert result is True
		assert "[...FILE DATA REDACTED...]" in record.msg
		assert "data:image/png;base64" not in record.msg

	def test_filter_redacts_image_url(self):
		"""Test that image URL base64 content is redacted."""
		log_filter = FileUploadFilter()

		record = logging.LogRecord(
			name="test",
			level=logging.INFO,
			pathname="test.py",
			lineno=1,
			msg="Image 'url': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...'",
			args=(),
			exc_info=None,
		)

		result = log_filter.filter(record)

		assert result is True
		assert "[...IMAGE DATA REDACTED...]" in record.msg
		assert "data:image/jpeg;base64" not in record.msg

	def test_filter_passes_normal_messages(self):
		"""Test that normal log messages pass through unchanged."""
		log_filter = FileUploadFilter()

		record = logging.LogRecord(
			name="test",
			level=logging.INFO,
			pathname="test.py",
			lineno=1,
			msg="Normal log message without file data",
			args=(),
			exc_info=None,
		)

		result = log_filter.filter(record)

		assert result is True
		assert record.msg == "Normal log message without file data"



class TestLogger:
	"""Test Logger initialization and configuration."""

	def test_logger_initialization_colorful(self):
		"""Test Logger initializes with colorful output."""
		with patch("ai_ticket_platform.core.logger.logger.logging.handlers.QueueListener"):
			logger = Logger(colorful_output=True)

			assert logger.colorful_output is True
			assert logger.queue_handler is not None
			assert logger.root_logger is not None

	def test_logger_initialization_json(self):
		"""Test Logger initializes with JSON output."""
		with patch("ai_ticket_platform.core.logger.logger.logging.handlers.QueueListener"):
			logger = Logger(colorful_output=False)

			assert logger.colorful_output is False
			assert logger.queue_handler is not None

	def test_logger_shutdown(self):
		"""Test Logger shutdown stops listener."""
		with patch("ai_ticket_platform.core.logger.logger.logging.handlers.QueueListener") as mock_listener_class:
			mock_listener = MagicMock()
			mock_listener_class.return_value = mock_listener

			logger = Logger()
			logger.shutdown()

			mock_listener.stop.assert_called_once()

	def test_logger_shutdown_removes_handler(self):
		"""Test Logger shutdown removes queue handler."""
		with patch("ai_ticket_platform.core.logger.logger.logging.handlers.QueueListener"):
			logger = Logger()
			initial_handlers = len(logger.root_logger.handlers)

			logger.shutdown()

			# Handler should be removed
			assert len(logger.root_logger.handlers) < initial_handlers


class TestLogContext:
	"""Test context-aware logging."""

	def test_add_context_to_log(self):
		"""Test adding context to log."""
		# Reset context
		LOG_CONTEXT.set({})

		with add_context_to_log(user_id="123", request_id="abc"):
			context = LOG_CONTEXT.get()
			assert context["user_id"] == "123"
			assert context["request_id"] == "abc"

		# Context should be cleared after exiting
		context_after = LOG_CONTEXT.get()
		assert "user_id" not in context_after
		assert "request_id" not in context_after

	def test_add_context_nested(self):
		"""Test nested context additions."""
		LOG_CONTEXT.set({})

		with add_context_to_log(level1="value1"):
			assert LOG_CONTEXT.get()["level1"] == "value1"

			with add_context_to_log(level2="value2"):
				context = LOG_CONTEXT.get()
				assert context["level1"] == "value1"
				assert context["level2"] == "value2"

			# level2 should be gone
			context = LOG_CONTEXT.get()
			assert "level1" in context
			assert "level2" not in context

	def test_add_context_overwrites(self):
		"""Test that context can be overwritten."""
		LOG_CONTEXT.set({})

		with add_context_to_log(key="value1"):
			assert LOG_CONTEXT.get()["key"] == "value1"

			with add_context_to_log(key="value2"):
				assert LOG_CONTEXT.get()["key"] == "value2"

			# Should revert to original
			assert LOG_CONTEXT.get()["key"] == "value1"
