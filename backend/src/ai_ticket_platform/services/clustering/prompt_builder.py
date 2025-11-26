# services/clustering/prompt_builder.py
from typing import List, Dict
from ai_ticket_platform.database.generated_models import Ticket


def build_batch_clustering_prompt(tickets: List[Ticket], existing_intents: List[Dict]) -> str:
	"""
	Build prompt for batch clustering decision.
	"""
	# Format existing intents
	if existing_intents:
		intent_list = "\n".join([
			f"ID: {intent['intent_id']} | {intent['intent_name']} | "
			f"({intent['category_l1_name']} > {intent['category_l2_name']} > {intent['category_l3_name']})"
			for intent in existing_intents
		])
		intent_section = f"""
EXISTING INTENTS:
{intent_list}

You can assign tickets to these existing intents ONLY if they match the specific issue very closely.
Otherwise, create NEW highly specific intents with all 3 category levels.
"""
	else:
		intent_section = """
There are NO existing intents in the system yet.
You MUST create NEW intents with all 3 category levels for each ticket.
"""

	# Format tickets
	ticket_list = "\n".join([
		f"[{i}] Subject: {ticket.subject}\n    Body: {ticket.body[:200]}{'...' if len(ticket.body) > 200 else ''}"
		for i, ticket in enumerate(tickets)
	])

	prompt = f"""
You are a support ticket categorization expert. Your task is to assign each ticket to an existing highly specific intent OR create new ones.

{intent_section}

TICKETS TO CATEGORIZE:
{ticket_list}

CLUSTERING GUIDELINES:

1. **Intents must be VERY SPECIFIC** - each intent represents ONE specific user question/issue
   - Good: "Password Reset via Email", "Unable to Download Invoice PDF", "API Rate Limit Exceeded"
   - Bad: "Password Issues", "Billing Problems", "API Issues"

2. **3-Tier Category Structure**:
   - Level 1 (Broad): Top-level product area (e.g., "Authentication", "Billing", "API Access")
   - Level 2 (Medium): Functional subcategory (e.g., "Password Management", "Invoices", "Rate Limiting")
   - Level 3 (Specific): Detailed issue type (e.g., "Email Reset", "PDF Download", "Quota Exceeded")

3. **Matching vs Creating**:
   - MATCH: Only if ticket describes the EXACT SAME specific issue as an existing intent
   - CREATE: If ticket is about a different specific issue, even if in same general area
   - When in doubt, CREATE a new intent to maintain specificity

4. **Category Naming**:
   - Use clear, concise names (2-4 words max per level)
   - Be consistent with existing category names when possible
   - New categories can reuse existing L1/L2 categories with a new L3

5. **Batch Processing**:
   - Process all {len(tickets)} tickets in this batch
   - If multiple tickets have the same specific issue, assign them to the SAME intent
   - Return one decision per ticket, using the ticket index [0], [1], [2], etc.

DECISION REQUIRED FOR EACH TICKET:
For each ticket, choose ONE option:
- Option A: Assign to existing intent (provide intent_id)
- Option B: Create new intent (provide all 3 category level names AND a descriptive intent_name)

The intent_name should be a brief, specific phrase describing the core issue:
- Good examples: "Login credentials rejected on mobile", "Payment declined - invalid card", "Password reset email not received"
- Bad examples: "Login problem", "Payment issue", "Password problem"

Return decisions for ALL {len(tickets)} tickets.
"""
	return prompt


def get_batch_clustering_schema() -> dict:
	"""
	Get the JSON schema for batch clustering output.
	"""
	return {
		"type": "object",
		"properties": {
			"assignments": {
				"type": "array",
				"description": "List of clustering decisions, one per ticket",
				"items": {
					"type": "object",
					"properties": {
						"ticket_index": {
							"type": "integer",
							"description": "Index of the ticket in the batch (0, 1, 2, ...)"
						},
						"decision": {
							"type": "string",
							"enum": ["match_existing", "create_new"],
							"description": "Whether to match existing intent or create new"
						},
						"intent_id": {
							"type": ["integer", "null"],
							"description": "ID of existing intent (required if decision is match_existing)"
						},
						"category_l1_name": {
							"type": ["string", "null"],
							"description": "Level 1 category name (required if creating new)"
						},
						"category_l2_name": {
							"type": ["string", "null"],
							"description": "Level 2 category name (required if creating new)"
						},
						"category_l3_name": {
							"type": ["string", "null"],
							"description": "Level 3 category name (required if creating new)"
						},
						"intent_name": {
							"type": ["string", "null"],
							"description": "Descriptive name for the intent (required if creating new) - should be a specific phrase describing the core issue"
						},
						"confidence": {
							"type": "number",
							"description": "Confidence score 0-1",
							"minimum": 0,
							"maximum": 1
						},
						"reasoning": {
							"type": "string",
							"description": "Brief explanation of the decision"
						}
					},
					"required": ["ticket_index", "decision", "confidence", "reasoning"],
					"additionalProperties": False,
					"allOf": [
						{
							"if": {
								"properties": {"decision": {"const": "match_existing"}}
							},
							"then": {
								"required": ["intent_id"]
							}
						},
						{
							"if": {
								"properties": {"decision": {"const": "create_new"}}
							},
							"then": {
								"required": ["category_l1_name", "category_l2_name", "category_l3_name", "intent_name"]
							}
						}
					]
				}
			}
		},
		"required": ["assignments"],
		"additionalProperties": False
	}


def get_task_config() -> dict:
	"""
	Get the task configuration for LLM call.
	"""
	return {
		"system_prompt": "You are an expert at categorizing support tickets into highly specific intents. Each intent should represent one specific user question or issue.",
		"schema_name": "batch_clustering"
	}
