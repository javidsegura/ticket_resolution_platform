"""
LLM Client for interacting with language models
Temporary stub implementation pending @catebros integration
"""

import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interfacing with LLM services"""

    def __init__(self, settings):
        """Initialize LLM client with settings"""
        self.settings = settings
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        logger.info(f"LLMClient initialized with model: {self.model}")

    def call(self, prompt: str, **kwargs) -> str:
        """Make a call to the LLM"""
        raise NotImplementedError("LLMClient.call() must be implemented by @catebros")

    def __repr__(self):
        return f"LLMClient(model={self.model})"
