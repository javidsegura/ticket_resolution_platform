# services/clustering/prompt_builder.py
from typing import List, Dict


def build_batch_clustering_prompt(tickets: List[Dict], existing_intents: List[Dict]) -> str:
	"""
	Build prompt for batch clustering decision.

	Args:
		tickets: List of ticket dicts with keys: id, subject, body
		existing_intents: List of existing intent dicts
	"""
	# Format existing intents
	if existing_intents:
		intent_list = "\n".join([
			f"ID: {intent.get('intent_id', 'N/A')} | {intent.get('intent_name', 'Unnamed')} | "
			f"({intent.get('category_l1_name', 'N/A')} > {intent.get('category_l2_name', 'N/A')} > {intent.get('category_l3_name', 'N/A')})"
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
		f"[{i}] Subject: {ticket.get('subject', '')}\n    Body: {ticket.get('body', '')[:200]}{'...' if len(ticket.get('body', '')) > 200 else ''}"
		for i, ticket in enumerate(tickets)
	])

	prompt = f"""
You are a support ticket categorization expert specializing in ULTRA-GRANULAR classification. Your mission: Create intents so specific that each one represents a single, exact user question with precise symptoms.

CRITICAL: Category Level 3 must be equivalent to the user's EXACT question. If someone asked "What's wrong?", the L3 category should be the specific answer.

{intent_section}

TICKETS TO CATEGORIZE:
{ticket_list}

CLUSTERING GUIDELINES:

1. **Intents must be ULTRA-SPECIFIC** - each intent represents ONE exact user question/issue
   - Good: "Password reset email not arriving in inbox", "Cannot download PDF invoice from portal", "API returning 429 rate limit error"
   - Bad: "Password Issues", "Invoice Problems", "API Errors"
   - Think: What EXACT question is the user asking?

2. **3-Tier Category Structure - HIGHLY GRANULAR**:

   **Level 1 (Broad Domain)**: Top-level product/service area
   - Examples: "Account & Authentication", "Billing & Payments", "API & Integrations", "Network & Connectivity"
   - Keep to 2-4 words, represents the major domain

   **Level 2 (Functional Area)**: Specific functional subcategory within the domain
   - Examples: "Password Recovery", "Invoice Management", "Rate Limiting", "VPN Access"
   - Keep to 2-4 words, represents a specific feature or component

   **Level 3 (EXACT ISSUE)**: The most granular level - should be equivalent to the exact question being asked
   - CRITICAL: L3 must be so specific that it describes the EXACT problem/symptom
   - Good L3 examples:
     * "Reset email not received" (NOT just "Email issues")
     * "PDF download fails with 404" (NOT just "Download problems")
     * "Expired token error on GET requests" (NOT just "Token errors")
     * "Two-factor code SMS delayed" (NOT just "2FA issues")
     * "Credit card declined - CVV mismatch" (NOT just "Payment declined")
   - Bad L3 examples (too broad):
     * "Login problems", "Email issues", "Download errors", "Token problems"
   - L3 should capture: specific action + specific failure/symptom
   - Think: If someone searches for this exact issue, would they find the right solution?

3. **Matching vs Creating**:
   - MATCH: Only if the ticket describes the EXACT SAME specific issue as an existing intent
     * Same root cause, same symptoms, same specific failure point
     * Example: Two tickets about "password reset email not received" → MATCH
     * Counter-example: "password reset email delayed" vs "password reset email not received" → CREATE NEW (different symptoms)
   - CREATE: If the ticket has ANY difference in the specific symptom or root cause
   - When in doubt, CREATE a new intent to maintain ultra-high specificity
   - Remember: Better to have 100 specific intents than 10 vague ones

4. **Category Naming Rules**:
   - Level 1: 2-4 words, general domain
   - Level 2: 2-4 words, specific feature/component
   - Level 3: 3-8 words, EXACT issue description (can be longer to capture specificity)
   - Be consistent with existing category names when possible
   - New categories can reuse existing L1/L2 categories with a new highly specific L3
   - Use concrete, actionable language in L3 (avoid vague terms like "issues", "problems", "errors" without specifics)

5. **Batch Processing**:
   - Process all {len(tickets)} tickets in this batch
   - If multiple tickets describe the EXACT SAME specific issue, assign them to the SAME intent
   - Return one decision per ticket, using the ticket index [0], [1], [2], etc.

DECISION REQUIRED FOR EACH TICKET:
For each ticket, choose ONE option:
- Option A: Assign to existing intent (provide intent_id)
- Option B: Create new intent (provide all 3 category level names AND a highly specific intent_name)

The intent_name should be an ultra-specific phrase describing the EXACT issue (mirror the L3 category specificity):
- EXCELLENT examples (very specific):
  * "Password reset link expired after 30 minutes"
  * "Invoice PDF download returns 404 error"
  * "API rate limit 429 error on /users endpoint"
  * "Two-factor authentication SMS code arrives 10+ minutes late"
  * "VPN connection drops every 5-10 minutes on WiFi"
  * "Shared drive access denied - permission error"
  * "Laptop freezes during startup at login screen"

- GOOD examples (specific enough):
  * "Password reset email not received in inbox"
  * "Credit card payment declined - CVV mismatch"
  * "Printer shows offline despite being powered on"

- BAD examples (too vague):
  * "Login problem", "Payment issue", "Password problem"
  * "Email not working", "Printer issues", "Network errors"

Remember: The intent_name is what users will see when searching for solutions. Make it specific enough that they immediately know if it matches their exact issue.

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
		"system_prompt": "You are an expert at categorizing support tickets into ultra-specific intents. Each intent must represent ONE exact, granular user question or issue with precise symptoms. Category Level 3 must be so specific that it describes the exact problem as if answering 'What is the user's exact question?' Avoid vague categorizations - specificity is paramount.",
		"schema_name": "batch_clustering"
	}
