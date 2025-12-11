import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from google.api_core.exceptions import GoogleAPIError

from ai_ticket_platform.core.clients.llm import LLMClient, initialize_llm_client


class TestLLMClient:
	"""Test suite for LLMClient class."""

	@pytest.fixture
	def mock_settings(self):
		"""Create mock settings object with required configuration."""
		settings = Mock()
		settings.GEMINI_API_KEY = "test-api-key-12345"
		settings.GEMINI_MODEL = "gemini-2.5-flash"
		return settings
	
	@pytest.fixture
	def llm_client(self, mock_settings):
		"""Create LLMClient instance with mocked settings."""
		with patch("ai_ticket_platform.core.clients.llm.genai.configure") as mock_configure, \
		     patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel", return_value=Mock()) as mock_model:
			client = LLMClient(mock_settings)
			mock_configure.assert_called_once_with(api_key="test-api-key-12345")
			mock_model.assert_called_once_with("gemini-2.5-flash")
		return client

	def test_init_with_valid_settings(self, mock_settings):
		"""Test LLMClient initialization with valid settings."""
		with patch("ai_ticket_platform.core.clients.llm.genai.configure") as mock_configure, \
		     patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel", return_value=Mock()) as mock_model:
			client = LLMClient(mock_settings)

			# verify Gemini client initialized with correct API key and model
			mock_configure.assert_called_once_with(api_key="test-api-key-12345")
			mock_model.assert_called_once_with("gemini-2.5-flash")

			# verify model is set correctly
			assert client.model == "gemini-2.5-flash"

	def test_init_without_api_key(self):
		"""Test LLMClient initialization fails without API key."""
		settings = Mock()
		settings.GEMINI_API_KEY = None
		settings.GEMINI_MODEL = "gemini-2.5-flash"

		with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
			LLMClient(settings)

	def test_call_llm_structured_success(self, llm_client):
		"""Test successful LLM call with structured output."""
		# setup mock response
		mock_response = Mock()
		mock_response.text = '{"result": "success", "value": 42}'

		llm_client.client.generate_content = Mock(return_value=mock_response)

		# define test inputs
		prompt = "Test prompt"
		output_schema = {
			"type": "object",
			"properties": {
				"result": {"type": "string"},
				"value": {"type": "number"}
			}
		}
		task_config = {
			"system_prompt": "You are a test assistant.",
			"schema_name": "test_schema"
		}

		# execute
		result = llm_client.call_llm_structured(
			prompt=prompt,
			output_schema=output_schema,
			task_config=task_config,
			temperature=0.5
		)

		# verify
		assert result == {"result": "success", "value": 42}

		# verify API call parameters
		llm_client.client.generate_content.assert_called_once()
		call_args = llm_client.client.generate_content.call_args
		assert call_args[1]["generation_config"]["response_mime_type"] == "application/json"
		assert call_args[1]["generation_config"]["temperature"] == 0.5
		assert "You are a test assistant." in call_args[1]["contents"]
		assert prompt in call_args[1]["contents"]
		assert json.dumps(output_schema) in call_args[1]["contents"]

	def test_call_llm_structured_json_decode_error_with_retry(self, llm_client):
		"""Test LLM call retries on JSON decode error."""
		# first call returns invalid JSON, second call succeeds
		mock_response_invalid = Mock()
		mock_response_invalid.text = 'invalid json {{'
		mock_response_valid = Mock()
		mock_response_valid.text = '{"status": "success"}'

		llm_client.client.generate_content = Mock(
			side_effect=[mock_response_invalid, mock_response_valid]
		)

		# execute
		result = llm_client.call_llm_structured(
			prompt="Test",
			output_schema={"type": "object"},
			max_retries=3
		)

		# verify successful result after retry
		assert result == {"status": "success"}
		assert llm_client.client.generate_content.call_count == 2

	def test_call_llm_structured_api_error_with_retry(self, llm_client):
		"""Test LLM call retries on API error."""
		mock_response = Mock()
		mock_response.text = '{"status": "success"}'

		llm_client.client.generate_content = Mock(
			side_effect=[GoogleAPIError("temporary"), mock_response]
		)

		# execute
		result = llm_client.call_llm_structured(
			prompt="Test",
			output_schema={"type": "object"},
			max_retries=3
		)

		# verify successful result after retry
		assert result == {"status": "success"}
		assert llm_client.client.generate_content.call_count == 2

	def test_call_llm_structured_api_error_exhausts_retries(self, llm_client):
		"""Test LLM call raises error after exhausting retries on JSON decode error."""
		# all calls return invalid JSON
		mock_response_bad = Mock()
		mock_response_bad.text = 'invalid json that will fail'

		llm_client.client.generate_content = Mock(
			return_value=mock_response_bad
		)

		# execute and verify exception
		import json
		with pytest.raises(json.JSONDecodeError):
			llm_client.call_llm_structured(
				prompt="Test",
				output_schema={"type": "object"},
				max_retries=2
			)

		# verify retried 2 times
		assert llm_client.client.generate_content.call_count == 2

class TestInitializeLLMClient:
	"""Test suite for initialize_llm_client function."""

	@pytest.fixture(autouse=True)
	def reset_global_client(self):
		"""Reset global LLM client before and after each test."""
		import ai_ticket_platform.core.clients.llm as llm_module
		original_client = llm_module.llm_client
		llm_module.llm_client = None
		yield
		llm_module.llm_client = original_client

	@pytest.fixture
	def mock_settings(self):
		"""Create mock settings object."""
		settings = Mock()
		settings.GEMINI_API_KEY = "test-api-key"
		settings.GEMINI_MODEL = "gemini-2.5-flash"
		return settings

	def test_initialize_llm_client_first_time(self, mock_settings):
		"""Test initializing LLM client for the first time."""
		import ai_ticket_platform.core.clients.llm as llm_module
		with patch("ai_ticket_platform.core.clients.llm.genai.configure"), \
		     patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel", return_value=Mock()):
			client = initialize_llm_client(mock_settings)

			# verify client was created
			assert client is not None
			assert isinstance(client, LLMClient)
			assert llm_module.llm_client is client

	def test_initialize_llm_client_singleton(self, mock_settings):
		"""Test LLM client follows singleton pattern."""
		import ai_ticket_platform.core.clients.llm as llm_module
		with patch("ai_ticket_platform.core.clients.llm.genai.configure"), \
		     patch("ai_ticket_platform.core.clients.llm.genai.GenerativeModel", return_value=Mock()):
			client1 = initialize_llm_client(mock_settings)
			client2 = initialize_llm_client(mock_settings)

			# verify same instance is returned
			assert client1 is client2
