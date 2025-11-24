"""Unit tests for clustering prompt builder."""

import pytest
from ai_ticket_platform.services.clustering.prompt_builder import (
    build_clustering_prompt,
    get_output_schema
)


class TestClusteringPromptBuilder:
    """Test clustering prompt generation."""

    def test_build_prompt_formats_ticket_list(self):
        """Test that prompt includes properly formatted ticket list."""
        tickets = ["Login Bug", "Password Reset"]
        prompt = build_clustering_prompt(tickets)

        assert "0. Login Bug" in prompt
        assert "1. Password Reset" in prompt
        assert f"Analyze the following {len(tickets)} support tickets" in prompt

    def test_build_prompt_includes_hierarchical_instructions(self):
        """Test that prompt includes hierarchical classification instructions."""
        tickets = ["Test Ticket"]
        prompt = build_clustering_prompt(tickets)

        assert "Product" in prompt
        assert "Category" in prompt
        assert "Subcategory" in prompt
        assert "HIERARCHICAL CLASSIFICATION" in prompt

    def test_build_prompt_includes_granularity_guidance(self):
        """Test that prompt emphasizes granular clustering."""
        tickets = ["Test Ticket"]
        prompt = build_clustering_prompt(tickets)

        assert "GRANULAR" in prompt
        assert "SPECIFIC" in prompt
        assert "granular clusters" in prompt

    def test_build_prompt_with_many_tickets(self):
        """Test prompt generation with many tickets."""
        tickets = [f"Ticket {i}" for i in range(50)]
        prompt = build_clustering_prompt(tickets)

        assert f"Analyze the following {len(tickets)} support tickets" in prompt
        assert "0. Ticket 0" in prompt
        assert "49. Ticket 49" in prompt

    def test_build_prompt_includes_examples(self):
        """Test that prompt includes example classifications."""
        tickets = ["Test"]
        prompt = build_clustering_prompt(tickets)

        assert "EXAMPLES OF GOOD CLUSTERING:" in prompt
        assert "Mobile App" in prompt
        assert "Authentication" in prompt
        assert "Biometric Login" in prompt

    def test_build_prompt_includes_rules(self):
        """Test that prompt includes important rules."""
        tickets = ["Test"]
        prompt = build_clustering_prompt(tickets)

        assert "IMPORTANT RULES:" in prompt
        assert "Every ticket must be assigned to exactly one cluster" in prompt
        assert "ticket indices" in prompt


class TestClusteringOutputSchema:
    """Test clustering output schema definition."""

    def test_output_schema_structure(self):
        """Test that output schema has correct structure."""
        schema = get_output_schema()

        assert schema["type"] == "object"
        assert "clusters" in schema["properties"]
        assert "required" in schema
        assert "clusters" in schema["required"]

    def test_cluster_item_required_fields(self):
        """Test that cluster items have all required fields."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        required_fields = cluster_schema["required"]
        assert "topic_name" in required_fields
        assert "product" in required_fields
        assert "category" in required_fields
        assert "subcategory" in required_fields
        assert "ticket_indices" in required_fields
        assert "summary" in required_fields

    def test_topic_name_field_description(self):
        """Test that topic_name field has proper description."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        topic_field = cluster_schema["properties"]["topic_name"]
        assert topic_field["type"] == "string"
        assert "description" in topic_field

    def test_product_field_definition(self):
        """Test that product field is properly defined."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        product_field = cluster_schema["properties"]["product"]
        assert product_field["type"] == "string"
        assert "product" in product_field["description"].lower()

    def test_category_field_definition(self):
        """Test that category field is properly defined."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        category_field = cluster_schema["properties"]["category"]
        assert category_field["type"] == "string"
        assert "functional" in category_field["description"].lower()

    def test_subcategory_field_definition(self):
        """Test that subcategory field is properly defined."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        subcat_field = cluster_schema["properties"]["subcategory"]
        assert subcat_field["type"] == "string"
        assert "specific" in subcat_field["description"].lower()

    def test_ticket_indices_field_definition(self):
        """Test that ticket_indices is array of integers."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        indices_field = cluster_schema["properties"]["ticket_indices"]
        assert indices_field["type"] == "array"
        assert indices_field["items"]["type"] == "integer"

    def test_summary_field_definition(self):
        """Test that summary field is properly defined."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        summary_field = cluster_schema["properties"]["summary"]
        assert summary_field["type"] == "string"
        assert "summary" in summary_field["description"].lower()

    def test_no_additional_properties_allowed(self):
        """Test that no additional properties are allowed."""
        schema = get_output_schema()
        cluster_schema = schema["properties"]["clusters"]["items"]

        assert cluster_schema.get("additionalProperties") is False

    def test_clusters_array_definition(self):
        """Test that clusters is properly defined as array."""
        schema = get_output_schema()
        clusters_field = schema["properties"]["clusters"]

        assert clusters_field["type"] == "array"
        assert "items" in clusters_field
        assert "description" in clusters_field
