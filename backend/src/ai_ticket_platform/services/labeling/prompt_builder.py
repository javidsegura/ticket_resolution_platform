def build_labeling_prompt(document_content: str, filename: str) -> str:
	"""
	Build prompt for document labeling.
	Content is already truncated by the decoder (max 25,000 chars from sequential pages).
	"""
	prompt = f"""
        Analyze the following company document and identify the primary department or area it belongs to.

        DOCUMENT FILENAME: {filename}

        DOCUMENT CONTENT:
        {document_content}

        TASK:
        Identify the PRIMARY department or area this document belongs to.
        This classification will be used to route support tickets to the correct professionals in the company.

        Return a SINGLE keyword that best represents the department/area.

        GUIDELINES:
        - Use 1-2 words maximum (e.g., "Tech", "Finance", "HR", "Marketing", "Legal", "Operations")
        - Be specific and clear
        - If the document covers technical aspects, use "Tech"
        - If it's finance-related (budgets, expenses, accounting), use "Finance"
        - If it's about employees, hiring, or benefits, use "HR"
        - Choose the area that would be most relevant for routing support questions about this document
        - You can propose any department/area name that makes sense for the document content

        EXAMPLES:
        - "API Integration Guide" → Tech
        - "Employee Expense Reimbursement Policy" → Finance
        - "Benefits Enrollment Process" → HR
        - "Sales Commission Structure" → Sales
    """

	return prompt


def get_output_schema() -> dict:
	"""
	Get the JSON schema for LLM structured output for document labeling.
	"""

	return {
		"type": "object",
		"properties": {
			"department_area": {
				"type": "string",
				"description": "Single keyword representing the primary department or area (1-2 words max)",
			}
		},
		"required": ["department_area"],
		"additionalProperties": False,
	}


def get_task_config() -> dict:
	return {
		"system_prompt": (
			"You are a document classification expert. "
			"Analyze company documents and identify the primary department or area they belong to. "
			"This classification helps route support tickets to the correct professionals."
		),
		"schema_name": "document_department_classification",
	}
