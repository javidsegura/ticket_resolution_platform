"""Unit tests for LLM client."""

import pytest
import json
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import GoogleAPIError


class TestLLMClientInit:
	"""Test LLMClient initialization."""

	def test_llm_client_init_success(self):
		"""Test successful LLM client initialization."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure") as mock_configure:
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_model_instance = MagicMock()
				mock_model.return_value = mock_model_instance

				client = LLMClient(mock_settings)

				assert client.model == "gemini-1.5-flash"
				assert client.client == mock_model_instance
				mock_configure.assert_called_once_with(api_key="test-api-key")
				mock_model.assert_called_once_with("gemini-1.5-flash")

	def test_llm_client_init_default_model(self):
		"""Test LLM client initialization with default model."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = None

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				client = LLMClient(mock_settings)

				assert client.model == "gemini-1.5-flash"
				mock_model.assert_called_once_with("gemini-1.5-flash")

	def test_llm_client_init_missing_api_key(self):
		"""Test that ValueError is raised when API key is missing."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = None

		with pytest.raises(ValueError) as exc_info:
			LLMClient(mock_settings)

		assert "GEMINI_API_KEY is required" in str(exc_info.value)


class TestCallLLMStructured:
	"""Test call_llm_structured method."""

	def test_call_llm_structured_success(self):
		"""Test successful structured LLM call."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_client = MagicMock()
				mock_model.return_value = mock_client

				mock_response = MagicMock()
				mock_response.text = '{"result": "success"}'
				mock_client.generate_content.return_value = mock_response

				client = LLMClient(mock_settings)
				result = client.call_llm_structured(
					prompt="Test prompt",
					output_schema={"type": "object"},
					temperature=0.5,
				)

				assert result == {"result": "success"}
				mock_client.generate_content.assert_called_once()

	def test_call_llm_structured_with_task_config(self):
		"""Test structured LLM call with custom task config."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_client = MagicMock()
				mock_model.return_value = mock_client

				mock_response = MagicMock()
				mock_response.text = '{"answer": 42}'
				mock_client.generate_content.return_value = mock_response

				client = LLMClient(mock_settings)
				result = client.call_llm_structured(
					prompt="What is the answer?",
					output_schema={"type": "object"},
					task_config={
						"system_prompt": "You are a calculator",
						"schema_name": "calculation"
					},
				)

				assert result == {"answer": 42}

	def test_call_llm_structured_empty_response(self):
		"""Test handling of empty response from LLM."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_client = MagicMock()
				mock_model.return_value = mock_client

				mock_response = MagicMock()
				mock_response.text = None
				mock_client.generate_content.return_value = mock_response

				client = LLMClient(mock_settings)

				with pytest.raises(ValueError) as exc_info:
					client.call_llm_structured(
						prompt="Test",
						output_schema={"type": "object"},
						max_retries=1,
					)

				assert "empty response" in str(exc_info.value)

	def test_call_llm_structured_json_decode_error_retry(self):
		"""Test retry logic on JSON decode error."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_client = MagicMock()
				mock_model.return_value = mock_client

				# First call returns invalid JSON, second call succeeds
				mock_response_1 = MagicMock()
				mock_response_1.text = "invalid json"
				mock_response_2 = MagicMock()
				mock_response_2.text = '{"status": "ok"}'

				mock_client.generate_content.side_effect = [mock_response_1, mock_response_2]

				client = LLMClient(mock_settings)
				result = client.call_llm_structured(
					prompt="Test",
					output_schema={"type": "object"},
					max_retries=2,
				)

				assert result == {"status": "ok"}
				assert mock_client.generate_content.call_count == 2

	def test_call_llm_structured_all_retries_fail(self):
		"""Test that exception is raised after all retries fail."""
		from ai_ticket_platform.core.clients.llm import LLMClient

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-api-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel") as mock_model:
				mock_client = MagicMock()
				mock_model.return_value = mock_client

				mock_client.generate_content.side_effect = GoogleAPIError("API error")

				client = LLMClient(mock_settings)

				with pytest.raises(GoogleAPIError):
					client.call_llm_structured(
						prompt="Test",
						output_schema={"type": "object"},
						max_retries=3,
					)

				assert mock_client.generate_content.call_count == 3


class TestInitializeLLMClient:
	"""Test initialize_llm_client function."""

	def test_initialize_llm_client_first_time(self):
		"""Test initializing LLM client for the first time."""
		from ai_ticket_platform.core.clients.llm import initialize_llm_client
		import ai_ticket_platform.core.clients.llm as llm_module

		# Reset global
		llm_module.llm_client = None

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel"):
				client = initialize_llm_client(mock_settings)

				assert client is not None
				assert llm_module.llm_client == client

	def test_initialize_llm_client_returns_existing(self):
		"""Test that existing LLM client is returned."""
		from ai_ticket_platform.core.clients.llm import initialize_llm_client
		import ai_ticket_platform.core.clients.llm as llm_module

		mock_existing_client = MagicMock()
		llm_module.llm_client = mock_existing_client

		mock_settings = MagicMock()
		client = initialize_llm_client(mock_settings)

		assert client == mock_existing_client


class TestGetLLMClient:
	"""Test get_llm_client function."""

	def test_get_llm_client_with_settings(self):
		"""Test getting LLM client with provided settings."""
		from ai_ticket_platform.core.clients.llm import get_llm_client
		import ai_ticket_platform.core.clients.llm as llm_module

		# Reset global
		llm_module.llm_client = None

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
			with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel"):
				client = get_llm_client(mock_settings)

				assert client is not None

	def test_get_llm_client_auto_initialize_settings(self):
		"""Test getting LLM client with auto-initialized settings."""
		from ai_ticket_platform.core.clients.llm import get_llm_client
		import ai_ticket_platform.core.clients.llm as llm_module

		# Reset global
		llm_module.llm_client = None

		mock_settings = MagicMock()
		mock_settings.GEMINI_API_KEY = "test-key"
		mock_settings.GEMINI_MODEL = "gemini-1.5-flash"

		# Patch initialize_settings where it's imported (inside get_llm_client function)
		with patch("ai_ticket_platform.core.settings.app_settings.initialize_settings", return_value=mock_settings):
			with patch("ai_ticket_platform.core.clients.llm.genai.configure"):
				with patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel"):
					client = get_llm_client()

					assert client is not None

	def test_get_llm_client_returns_existing(self):
		"""Test that existing client is returned."""
		from ai_ticket_platform.core.clients.llm import get_llm_client
		import ai_ticket_platform.core.clients.llm as llm_module

		mock_existing_client = MagicMock()
		llm_module.llm_client = mock_existing_client

		client = get_llm_client()

		assert client == mock_existing_client
