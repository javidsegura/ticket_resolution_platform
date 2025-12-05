from typing import Dict
import logging

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.company_docs import prompt_builder

logger = logging.getLogger(__name__)


def label_document(document: Dict, llm_client: LLMClient) -> Dict:
	"""
	Label a document to identify its department/area using LLM.
	"""
	filename = document.get("filename", "unknown")
	content = document.get("content", "")

	if not content.strip():
		return {
			"filename": filename,
			"department_area": "Unknown",
			"error": "Document content is empty",
		}

	try:
		# Build prompt and get schema and config
		prompt = prompt_builder.build_labeling_prompt(
			document_content=content, filename=filename
		)
		output_schema = prompt_builder.get_output_schema()
		task_config = prompt_builder.get_task_config()

		# Call LLM with structured output
		result = llm_client.call_llm_structured(
			prompt=prompt,
			output_schema=output_schema,
			task_config=task_config,
			temperature=0.3,
		)

		# Validate result structure
		if not isinstance(result, dict) or "department_area" not in result:
			logger.error(f"LLM returned invalid structure for document {filename}")
			return {
				"filename": filename,
				"department_area": "Unknown",
				"error": "LLM returned invalid response structure",
			}

		result["filename"] = filename
		return result
	except Exception as e:
		logger.error(f"Error labeling document {filename}: {str(e)}")
		return {"filename": filename, "department_area": "Unknown", "error": str(e)}
