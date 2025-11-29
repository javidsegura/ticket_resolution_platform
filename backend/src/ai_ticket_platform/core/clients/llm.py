import json
import logging
from typing import Dict

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

llm_client = None


class LLMClient:
	def __init__(self, settings):
		"""
		Initialize Gemini client using application settings.

		Args:
			settings: Application settings object containing LLM configuration (GEMINI_API_KEY, GEMINI_MODEL)
		"""
		api_key = getattr(settings, "GEMINI_API_KEY", None)
		if not api_key:
			raise ValueError("GEMINI_API_KEY is required but not set in environment variables")

		self.model = getattr(settings, "GEMINI_MODEL", None) or "gemini-1.5-flash"

		genai.configure(api_key=api_key)
		self.client = genai.GenerativeModel(self.model)

	def call_llm_structured(
		self,
		prompt: str,
		output_schema: Dict,
		task_config: Dict = None,
		temperature: float = 0.3,
		max_retries: int = 3
	) -> Dict:
		"""
		Call Gemini with structured output (JSON response).

		Args:
			prompt: The user prompt
			output_schema: JSON schema for expected output
			task_config: Optional dict with 'system_prompt' and 'schema_name' keys. Defaults to generic assistant behavior if not provided.
			temperature: Sampling temperature (0.0-1.0)
			max_retries: Number of retries on failure

		Returns:
			Parsed JSON response matching the schema
		"""
		if task_config is None:
			task_config = {}

		system_prompt = task_config.get("system_prompt", "You are a helpful AI assistant.")
		schema_name = task_config.get("schema_name", "response")

		logger.debug(f"Calling LLM with model {self.model}, temperature {temperature}, schema_name {schema_name}")

		schema_instruction = f"Return a JSON response that matches this JSON schema (strict): {json.dumps(output_schema)}"
		combined_prompt = f"{system_prompt}\n\n{schema_instruction}\n\nUser prompt:\n{prompt}"

		for attempt in range(max_retries):
			try:
				response = self.client.generate_content(
					contents=combined_prompt,
					generation_config={
						"temperature": temperature,
						"response_mime_type": "application/json"
					}
				)

				if not getattr(response, "text", None):
					logger.error("Gemini API returned empty response text")
					raise ValueError("Gemini API returned empty response text")

				result = json.loads(response.text)
				logger.info(f"Successfully received and parsed LLM response for schema {schema_name}")

				return result

			except (json.JSONDecodeError, GoogleAPIError, ValueError) as e:
				logger.warning(f"LLM call attempt {attempt + 1}/{max_retries} failed: {e}")
				if attempt == max_retries - 1:
					logger.error(f"All {max_retries} LLM call attempts failed")
					raise


def initialize_llm_client(settings):
	"""
	Initialize the global LLM client instance

	Args:
		settings: Application settings object containing LLM configuration

	Returns: LLMClient instance
	"""
	global llm_client
	logger.debug("Initializing LLM client")
	if not llm_client:
		logger.debug("Instantiate LLM client for the first time")
		llm_client = LLMClient(settings)
	return llm_client
