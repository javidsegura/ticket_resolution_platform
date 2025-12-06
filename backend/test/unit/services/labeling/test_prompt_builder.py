import pytest

from ai_ticket_platform.services.company_docs.prompt_builder import (
	build_labeling_prompt,
	get_output_schema,
	get_task_config,
)


class TestBuildLabelingPrompt:
	"""Test suite for build_labeling_prompt function."""

	def test_build_labeling_prompt_basic(self):
		"""Test basic prompt building with simple content."""
		# setup
		document_content = "This is a technical API documentation."
		filename = "api_guide.pdf"

		# execute
		prompt = build_labeling_prompt(document_content, filename)

		# verify
		assert isinstance(prompt, str)
		assert filename in prompt
		assert "This is a technical API documentation." in prompt
		assert "DOCUMENT FILENAME:" in prompt
		assert "DOCUMENT CONTENT" in prompt

	def test_build_labeling_prompt_includes_instructions(self):
		"""Test that prompt includes labeling instructions."""
		# setup
		document_content = "Employee handbook"
		filename = "hr_handbook.pdf"

		# execute
		prompt = build_labeling_prompt(document_content, filename)

		# verify prompt contains key instructions
		assert "TASK:" in prompt
		assert "department" in prompt.lower() or "area" in prompt.lower()
		assert "GUIDELINES:" in prompt
		assert "EXAMPLES:" in prompt


class TestGetOutputSchema:
	"""Test suite for get_output_schema function."""

	def test_get_output_schema_structure(self):
		"""Test that output schema has correct structure."""
		# execute
		schema = get_output_schema()

		# verify
		assert isinstance(schema, dict)
		assert schema["type"] == "object"
		assert "properties" in schema
		assert "required" in schema

	def test_get_output_schema_properties(self):
		"""Test that schema includes department_area property."""
		# execute
		schema = get_output_schema()

		# verify
		assert "department_area" in schema["properties"]
		assert schema["properties"]["department_area"]["type"] == "string"
		assert "description" in schema["properties"]["department_area"]

	def test_get_output_schema_required_fields(self):
		"""Test that department_area is required in schema."""
		# execute
		schema = get_output_schema()

		# verify
		assert "department_area" in schema["required"]

	def test_get_output_schema_no_additional_properties(self):
		"""Test that schema restricts additional properties."""
		# execute
		schema = get_output_schema()

		# verify
		assert schema["additionalProperties"] is False


class TestGetTaskConfig:
	"""Test suite for get_task_config function."""

	def test_get_task_config_structure(self):
		"""Test that task config has correct structure."""
		# execute
		config = get_task_config()

		# verify
		assert isinstance(config, dict)
		assert "system_prompt" in config
		assert "schema_name" in config

	def test_get_task_config_system_prompt(self):
		"""Test that system prompt is appropriate for classification."""
		# execute
		config = get_task_config()

		# verify
		system_prompt = config["system_prompt"]
		assert isinstance(system_prompt, str)
		assert len(system_prompt) > 0
		# should mention document classification or similar concept
		assert "document" in system_prompt.lower() or "classification" in system_prompt.lower()

	def test_get_task_config_schema_name(self):
		"""Test that schema name is defined."""
		# execute
		config = get_task_config()

		# verify
		schema_name = config["schema_name"]
		assert isinstance(schema_name, str)
		assert len(schema_name) > 0
		assert "document_department_classification" == schema_name
