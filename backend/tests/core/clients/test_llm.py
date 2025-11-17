import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from openai import OpenAI

from ai_ticket_platform.core.clients.llm import LLMClient, initialize_llm_client


class TestLLMClient:
	"""Test suite for LLMClient class."""

	@pytest.fixture
	def mock_settings(self):
		"""Create mock settings object with required configuration."""
		settings = Mock()
		settings.OPENAI_API_KEY = "test-api-key-12345"
		settings.OPENAI_MODEL = "gpt-4o"
		return settings
	
	@pytest.fixture
	def llm_client(self, mock_settings):
		"""Create LLMClient instance with mocked settings."""
		with patch.object(OpenAI, '__init__', return_value=None):
			client = LLMClient(mock_settings)
			client.client = Mock()
		return client

	def test_init_with_valid_settings(self, mock_settings):
		"""Test LLMClient initialization with valid settings."""
		with patch.object(OpenAI, '__init__', return_value=None) as mock_openai_init:
			client = LLMClient(mock_settings)

			# verify OpenAI client initialized with correct API key
			mock_openai_init.assert_called_once_with(api_key="test-api-key-12345")

			# verify model is set correctly
			assert client.model == "gpt-4o"

	def test_init_without_api_key(self):
		"""Test LLMClient initialization fails without API key."""
		settings = Mock()
		settings.OPENAI_API_KEY = None
		settings.OPENAI_MODEL = "gpt-4o"

		with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
			LLMClient(settings)

	def test_call_llm_structured_success(self, llm_client):
		"""Test successful LLM call with structured output."""
		# setup mock response
		mock_message = Mock()
		mock_message.content = '{"result": "success", "value": 42}'
		mock_choice = Mock()
		mock_choice.message = mock_message
		mock_response = Mock()
		mock_response.choices = [mock_choice]

		llm_client.client.chat.completions.create = Mock(return_value=mock_response)

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
		llm_client.client.chat.completions.create.assert_called_once()
		call_args = llm_client.client.chat.completions.create.call_args

		assert call_args[1]["model"] == "gpt-4o"
		assert call_args[1]["temperature"] == 0.5
		assert call_args[1]["messages"][0]["role"] == "system"
		assert call_args[1]["messages"][0]["content"] == "You are a test assistant."
		assert call_args[1]["messages"][1]["role"] == "user"
		assert call_args[1]["messages"][1]["content"] == prompt
		assert call_args[1]["response_format"]["type"] == "json_schema"
		assert call_args[1]["response_format"]["json_schema"]["name"] == "test_schema"
		assert call_args[1]["response_format"]["json_schema"]["schema"] == output_schema
		assert call_args[1]["response_format"]["json_schema"]["strict"] is True

	def test_call_llm_structured_json_decode_error_with_retry(self, llm_client):
		"""Test LLM call retries on JSON decode error."""
		# first call returns invalid JSON, second call succeeds
		mock_message_invalid = Mock()
		mock_message_invalid.content = 'invalid json {{'
		mock_choice_invalid = Mock()
		mock_choice_invalid.message = mock_message_invalid
		mock_response_invalid = Mock()
		mock_response_invalid.choices = [mock_choice_invalid]

		mock_message_valid = Mock()
		mock_message_valid.content = '{"status": "success"}'
		mock_choice_valid = Mock()
		mock_choice_valid.message = mock_message_valid
		mock_response_valid = Mock()
		mock_response_valid.choices = [mock_choice_valid]

		llm_client.client.chat.completions.create = Mock(
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
		assert llm_client.client.chat.completions.create.call_count == 2

	def test_call_llm_structured_api_error_with_retry(self, llm_client):
		"""Test LLM call retries on API error."""
		# first call raises exception, second succeeds
		mock_message = Mock()
		mock_message.content = '{"status": "success"}'
		mock_choice = Mock()
		mock_choice.message = mock_message
		mock_response = Mock()
		mock_response.choices = [mock_choice]

		llm_client.client.chat.completions.create = Mock(
			side_effect=[Exception("API Error"), mock_response]
		)

		# execute
		result = llm_client.call_llm_structured(
			prompt="Test",
			output_schema={"type": "object"},
			max_retries=3
		)

		# verify successful result after retry
		assert result == {"status": "success"}
		assert llm_client.client.chat.completions.create.call_count == 2

	def test_call_llm_structured_api_error_exhausts_retries(self, llm_client):
		"""Test LLM call raises error after exhausting retries on API error."""
		# all calls raise exception
		llm_client.client.chat.completions.create = Mock(
			side_effect=Exception("Persistent API Error")
		)

		# execute and verify exception
		with pytest.raises(Exception, match="Persistent API Error"):
			llm_client.call_llm_structured(
				prompt="Test",
				output_schema={"type": "object"},
				max_retries=2
			)

		# verify retried 2 times
		assert llm_client.client.chat.completions.create.call_count == 2

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
		settings.OPENAI_API_KEY = "test-api-key"
		settings.OPENAI_MODEL = "gpt-4o"
		return settings

	def test_initialize_llm_client_first_time(self, mock_settings):
		"""Test initializing LLM client for the first time."""
		import ai_ticket_platform.core.clients.llm as llm_module
		with patch.object(OpenAI, '__init__', return_value=None):
			client = initialize_llm_client(mock_settings)

			# verify client was created
			assert client is not None
			assert isinstance(client, LLMClient)
			assert llm_module.llm_client is client

	def test_initialize_llm_client_singleton(self, mock_settings):
		"""Test LLM client follows singleton pattern."""
		import ai_ticket_platform.core.clients.llm as llm_module
		with patch.object(OpenAI, '__init__', return_value=None):
			client1 = initialize_llm_client(mock_settings)
			client2 = initialize_llm_client(mock_settings)

			# verify same instance is returned
			assert client1 is client2