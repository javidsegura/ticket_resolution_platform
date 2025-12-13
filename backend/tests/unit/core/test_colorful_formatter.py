"""Unit tests for ColoredJSONFormatter."""

import logging
import json
from ai_ticket_platform.core.logger.colorfulFormatter import ColoredJSONFormatter, Colors


class TestColoredJSONFormatter:
	"""Test ColoredJSONFormatter output formatting."""

	def test_formatter_basic_log(self):
		"""Test formatting a basic log record."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test.module",
			level=logging.INFO,
			pathname="test.py",
			lineno=1,
			msg="Test message",
			args=(),
			exc_info=None,
		)

		formatted = formatter.format(record)

		assert "test.module" in formatted
		assert "Test message" in formatted
		assert "INFO" in formatted
		assert "ℹ️" in formatted  # INFO emoji

	def test_formatter_debug_level(self):
		"""Test formatting DEBUG level."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test",
			level=logging.DEBUG,
			pathname="test.py",
			lineno=1,
			msg="Debug message",
			args=(),
			exc_info=None,
		)

		formatted = formatter.format(record)

		assert "DEBUG" in formatted
		assert "🐞" in formatted  # DEBUG emoji

	def test_formatter_warning_level(self):
		"""Test formatting WARNING level."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test",
			level=logging.WARNING,
			pathname="test.py",
			lineno=1,
			msg="Warning message",
			args=(),
			exc_info=None,
		)

		formatted = formatter.format(record)

		assert "WARNING" in formatted
		assert "⚠️" in formatted  # WARNING emoji

	def test_formatter_error_level(self):
		"""Test formatting ERROR level."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test",
			level=logging.ERROR,
			pathname="test.py",
			lineno=1,
			msg="Error message",
			args=(),
			exc_info=None,
		)

		formatted = formatter.format(record)

		assert "ERROR" in formatted
		assert "❌" in formatted  # ERROR emoji

	def test_formatter_critical_level(self):
		"""Test formatting CRITICAL level."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test",
			level=logging.CRITICAL,
			pathname="test.py",
			lineno=1,
			msg="Critical message",
			args=(),
			exc_info=None,
		)

		formatted = formatter.format(record)

		assert "CRITICAL" in formatted
		assert "🔥" in formatted  # CRITICAL emoji

	def test_formatter_with_context_fields(self):
		"""Test formatting with additional context fields."""
		formatter = ColoredJSONFormatter(
			"%(asctime)s %(name)s %(levelname)s %(message)s",
			rename_fields={"levelname": "level", "asctime": "time"},
		)

		record = logging.LogRecord(
			name="test",
			level=logging.INFO,
			pathname="test.py",
			lineno=1,
			msg="Message with context",
			args=(),
			exc_info=None,
		)

		# Add custom fields
		record.user_id = "123"
		record.request_id = "abc"

		formatted = formatter.format(record)

		assert "user_id" in formatted
		assert "123" in formatted
		assert "request_id" in formatted
		assert "abc" in formatted


class TestColors:
	"""Test Colors class constants."""

	def test_colors_defined(self):
		"""Test that all color constants are defined."""
		assert Colors.RESET is not None
		assert Colors.RED is not None
		assert Colors.GREEN is not None
		assert Colors.YELLOW is not None
		assert Colors.BLUE is not None
		assert Colors.CYAN is not None
		assert Colors.MAGENTA is not None
		assert Colors.BOLD is not None
