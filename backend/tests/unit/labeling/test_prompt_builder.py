"""Unit tests for labeling prompt builder."""

import pytest
from ai_ticket_platform.services.labeling.prompt_builder import (
    build_labeling_prompt,
    get_output_schema,
    get_task_config
)


class TestLabelingPromptBuilder:
    """Test document labeling prompt generation."""

    def test_build_prompt_includes_filename(self):
        """Test that prompt includes document filename."""
        prompt = build_labeling_prompt("Document content", "budget.pdf")
        assert "budget.pdf" in prompt
        assert "DOCUMENT FILENAME:" in prompt

    def test_build_prompt_includes_document_content(self):
        """Test that prompt includes document content."""
        content = "This is a technical specification document"
        prompt = build_labeling_prompt(content, "spec.pdf")
        assert content in prompt
        assert "DOCUMENT CONTENT:" in prompt

    def test_build_prompt_includes_task_description(self):
        """Test that prompt includes task description."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        # Check for task section and primary department mention
        assert "TASK:" in prompt
        assert "primary department" in prompt.lower() or "department" in prompt.lower()

    def test_build_prompt_includes_guidelines(self):
        """Test that prompt includes classification guidelines."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        assert "GUIDELINES:" in prompt
        assert "1-2 words maximum" in prompt

    def test_build_prompt_includes_examples(self):
        """Test that prompt includes example classifications."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        assert "EXAMPLES:" in prompt
        assert "API Integration Guide" in prompt
        assert "Tech" in prompt
        assert "Finance" in prompt
        assert "HR" in prompt
        assert "Sales" in prompt

    def test_build_prompt_mentions_return_format(self):
        """Test that prompt mentions return format."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        assert "SINGLE keyword" in prompt

    def test_build_prompt_with_special_characters_in_filename(self):
        """Test prompt generation with special characters in filename."""
        prompt = build_labeling_prompt("Content", "File@2024-01-15.pdf")
        assert "File@2024-01-15.pdf" in prompt

    def test_build_prompt_with_long_content(self):
        """Test prompt generation with very long document content."""
        long_content = "X" * 10000
        prompt = build_labeling_prompt(long_content, "long.pdf")
        assert long_content in prompt

    def test_build_prompt_mentions_routing_purpose(self):
        """Test that prompt explains routing purpose."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        assert "route support tickets" in prompt or "routing" in prompt.lower()

    def test_build_prompt_mentions_specific_areas(self):
        """Test that prompt mentions specific department areas."""
        prompt = build_labeling_prompt("Content", "test.pdf")
        assert "Tech" in prompt
        assert "Finance" in prompt
        assert "HR" in prompt
        assert "Marketing" in prompt
        assert "Legal" in prompt
        assert "Operations" in prompt


class TestLabelingOutputSchema:
    """Test document labeling output schema."""

    def test_output_schema_structure(self):
        """Test that output schema has correct structure."""
        schema = get_output_schema()
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_output_schema_has_department_area(self):
        """Test that schema includes department_area field."""
        schema = get_output_schema()
        assert "department_area" in schema["properties"]

    def test_department_area_is_string(self):
        """Test that department_area is string type."""
        schema = get_output_schema()
        dept_field = schema["properties"]["department_area"]
        assert dept_field["type"] == "string"

    def test_department_area_has_description(self):
        """Test that department_area has description."""
        schema = get_output_schema()
        dept_field = schema["properties"]["department_area"]
        assert "description" in dept_field
        assert "keyword" in dept_field["description"].lower()

    def test_department_area_is_required(self):
        """Test that department_area is in required fields."""
        schema = get_output_schema()
        assert "department_area" in schema["required"]

    def test_no_additional_properties(self):
        """Test that no additional properties are allowed."""
        schema = get_output_schema()
        assert schema.get("additionalProperties") is False


class TestLabelingTaskConfig:
    """Test document labeling task configuration."""

    def test_task_config_has_system_prompt(self):
        """Test that task config includes system prompt."""
        config = get_task_config()
        assert "system_prompt" in config

    def test_system_prompt_mentions_classification(self):
        """Test that system prompt mentions classification task."""
        config = get_task_config()
        assert "classification" in config["system_prompt"].lower()

    def test_system_prompt_mentions_documents(self):
        """Test that system prompt mentions document analysis."""
        config = get_task_config()
        assert "document" in config["system_prompt"].lower()

    def test_system_prompt_mentions_departments(self):
        """Test that system prompt mentions department classification."""
        config = get_task_config()
        assert "department" in config["system_prompt"].lower()

    def test_task_config_has_schema_name(self):
        """Test that task config includes schema name."""
        config = get_task_config()
        assert "schema_name" in config

    def test_schema_name_is_descriptive(self):
        """Test that schema name is descriptive."""
        config = get_task_config()
        schema_name = config["schema_name"]
        assert "document" in schema_name.lower()
        assert "classification" in schema_name.lower() or "department" in schema_name.lower()

    def test_system_prompt_mentions_routing(self):
        """Test that system prompt mentions routing."""
        config = get_task_config()
        assert "route" in config["system_prompt"].lower() or "routing" in config["system_prompt"].lower()

    def test_system_prompt_mentions_professionals(self):
        """Test that system prompt mentions routing to professionals."""
        config = get_task_config()
        assert "professional" in config["system_prompt"].lower()
