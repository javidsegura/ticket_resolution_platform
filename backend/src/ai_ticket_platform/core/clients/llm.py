from openai import OpenAI, APIError
import json
from typing import Dict
import logging

logger = logging.getLogger(__name__)

llm_client = None


class LLMClient():
    def __init__(self, settings):
        """
        Initialize LLM client using application settings.

        Args:
            settings: Application settings object containing LLM configuration (OPENAI_API_KEY, OPENAI_MODEL)
        """
        # Extract settings
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required but not set in environment variables")

        self.model = settings.OPENAI_MODEL or "gpt-4o"

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

    def call_llm_structured(self, prompt: str, output_schema: Dict, task_config: Dict = None, temperature: float = 0.3, max_retries: int = 3) -> Dict:
        """
        Call LLM with structured output (guaranteed JSON format).

        Args:
            prompt: The user prompt
            output_schema: JSON schema for expected output
            task_config: Optional dict with 'system_prompt' and 'schema_name' keys. Defaults to generic assistant behavior if not provided.
            temperature: Sampling temperature (0.0-1.0)
            max_retries: Number of retries on failure

        Returns:
            Parsed JSON response matching the schema
        """
        # Set defaults if task_config not provided
        if task_config is None:
            task_config = {}

        system_prompt = task_config.get("system_prompt", "You are a helpful AI assistant.")
        schema_name = task_config.get("schema_name", "response")

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "schema": output_schema,
                            "strict": True
                        }
                    },
                    temperature=temperature
                )

                if not response.choices:
                    raise ValueError("OpenAI API returned empty choices list")

                # parse response
                result = json.loads(response.choices[0].message.content)

                return result

            except (json.JSONDecodeError, APIError) as e:
                logger.warning(f"LLM call attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
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
