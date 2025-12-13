"""Unit tests for clustering prompt builder."""


class TestBuildBatchClusteringPrompt:
	"""Test build_batch_clustering_prompt function."""

	def test_build_prompt_with_existing_intents(self):
		"""Test building prompt with existing intents."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			build_batch_clustering_prompt,
		)

		tickets = [
			{"subject": "Login issue", "body": "Cannot log in"},
			{"subject": "Password reset", "body": "Need to reset password"},
		]

		existing_intents = [
			{
				"intent_id": 1,
				"intent_name": "Login problems",
				"category_l1_name": "Authentication",
				"category_l2_name": "Login",
				"category_l3_name": "Access issues",
			},
		]

		prompt = build_batch_clustering_prompt(tickets, existing_intents)

		assert "EXISTING INTENTS:" in prompt
		assert "ID: 1" in prompt
		assert "Login problems" in prompt
		assert "Login issue" in prompt
		assert "Password reset" in prompt
		assert f"{len(tickets)} tickets" in prompt

	def test_build_prompt_without_existing_intents(self):
		"""Test building prompt without existing intents."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			build_batch_clustering_prompt,
		)

		tickets = [
			{"subject": "Bug report", "body": "System crash"},
		]

		prompt = build_batch_clustering_prompt(tickets, [])

		assert "NO existing intents" in prompt
		assert "Bug report" in prompt
		assert "System crash" in prompt

	def test_build_prompt_truncates_long_body(self):
		"""Test that long ticket bodies are truncated."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			build_batch_clustering_prompt,
		)

		long_body = "x" * 300
		tickets = [
			{"subject": "Test", "body": long_body},
		]

		prompt = build_batch_clustering_prompt(tickets, [])

		# Body should be truncated to 200 chars plus '...'
		assert "..." in prompt
		assert long_body not in prompt


class TestGetBatchClusteringSchema:
	"""Test get_batch_clustering_schema function."""

	def test_get_schema_returns_valid_dict(self):
		"""Test that schema is returned as valid dict."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			get_batch_clustering_schema,
		)

		schema = get_batch_clustering_schema()

		assert isinstance(schema, dict)
		assert "type" in schema
		assert schema["type"] == "object"
		assert "properties" in schema
		assert "assignments" in schema["properties"]

	def test_schema_has_required_fields(self):
		"""Test that schema has all required fields."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			get_batch_clustering_schema,
		)

		schema = get_batch_clustering_schema()

		assignments_schema = schema["properties"]["assignments"]["items"]
		assert "ticket_index" in assignments_schema["properties"]
		assert "decision" in assignments_schema["properties"]
		assert "confidence" in assignments_schema["properties"]
		assert "reasoning" in assignments_schema["properties"]


class TestGetTaskConfig:
	"""Test get_task_config function."""

	def test_get_task_config_returns_dict(self):
		"""Test that task config is returned as dict."""
		from ai_ticket_platform.services.clustering.prompt_builder import (
			get_task_config,
		)

		config = get_task_config()

		assert isinstance(config, dict)
		assert "system_prompt" in config
		assert "schema_name" in config
		assert config["schema_name"] == "batch_clustering"
		assert "ultra-specific" in config["system_prompt"]
