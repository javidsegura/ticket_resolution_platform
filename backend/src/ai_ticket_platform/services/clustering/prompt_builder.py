from typing import List


def build_clustering_prompt(ticket_texts: List[str]) -> str:
    """
    Build optimized prompt for clustering.

    Args:
        ticket_texts: List of ticket text strings

    Returns:
        Formatted prompt string for LLM
    """

    # format tickets with indices
    ticket_list = "\n".join([
        f"{i}. {text}"
        for i, text in enumerate(ticket_texts)
    ])

    prompt = f"""
                Analyze the following {len(ticket_texts)} support tickets and cluster them into GRANULAR, SPECIFIC groups based on a hierarchical Product->Category->Subcategory structure.

                TICKETS:
                {ticket_list}

                HIERARCHICAL CLASSIFICATION:
                You MUST classify each cluster using this 3-level hierarchy:

                1. PRODUCT (Top Level) - The specific product, service, or feature area
                   Examples: "Mobile App", "Web Dashboard", "Payment Gateway", "Email Service", "Shopping Cart", "User Account System"

                2. CATEGORY (Middle Level) - The functional area within that product
                   Examples: "Authentication", "Notifications", "Performance", "UI/UX", "Data Sync", "Checkout Flow"

                3. SUBCATEGORY (Bottom Level) - The specific issue type or feature
                   Examples: "Password Reset", "Push Notifications", "Loading Speed", "Button Layout", "Cloud Backup", "Payment Processing"

                CLUSTERING INSTRUCTIONS:
                1. Create SPECIFIC, NARROW clusters - avoid broad groupings
                2. Each cluster should represent a very specific issue or topic
                3. Split broad themes into multiple granular clusters based on the Product → Category → Subcategory hierarchy
                4. Group tickets by their specific product/feature first, then by issue type
                5. Each ticket belongs to exactly ONE cluster
                6. Aim for 15-30 clusters for 100 tickets (more granular than before)
                7. Each cluster should have a clear, specific topic name

                EXAMPLES OF GOOD CLUSTERING:
                - Product: "Mobile App" | Category: "Authentication" | Subcategory: "Biometric Login" | Topic: "Face ID not working on iOS"
                - Product: "Shopping Cart" | Category: "Checkout" | Subcategory: "Payment Methods" | Topic: "Cannot add PayPal as payment option"
                - Product: "Email Service" | Category: "Delivery" | Subcategory: "Spam Filter" | Topic: "Legitimate emails going to spam"

                EXAMPLES OF TOO BROAD (AVOID):
                - Category: "Orders" | Subcategory: "Delivery" - TOO BROAD, split by specific products and delivery issues
                - Category: "Technical Support" | Subcategory: "Bugs" - TOO VAGUE, specify the product and exact bug type

                IMPORTANT RULES:
                - Every ticket must be assigned to exactly one cluster
                - Use ticket indices (0, 1, 2, ...) to reference tickets
                - Create descriptive topic names that clearly identify the specific issue
                - The Product field should identify the actual product/service/feature being discussed
                - Categories should be functional areas, not vague labels
                - Subcategories should pinpoint the exact type of issue
                - Prioritize granularity over simplicity - more specific clusters are better
            """

    return prompt


def get_output_schema() -> dict:
    """
    Get the JSON schema for LLM structured output.
    """

    return {
        "type": "object",
        "properties": {
            "clusters": {
                "type": "array",
                "description": "List of granular ticket clusters with hierarchical classification",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic_name": {
                            "type": "string",
                            "description": "Clear, specific name for this cluster topic (e.g., 'Cannot reset password via email')"
                        },
                        "product": {
                            "type": "string",
                            "description": "The specific product, service, or feature area (e.g., 'Mobile App', 'Payment Gateway', 'Shopping Cart')"
                        },
                        "category": {
                            "type": "string",
                            "description": "Functional area within the product (e.g., 'Authentication', 'Checkout Flow', 'Notifications')"
                        },
                        "subcategory": {
                            "type": "string",
                            "description": "Specific issue type or feature (e.g., 'Password Reset', 'Payment Processing', 'Push Notifications')"
                        },
                        "ticket_indices": {
                            "type": "array",
                            "description": "Array of ticket indices (integers) belonging to this cluster",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of the specific issue in this cluster"
                        }
                    },
                    "required": [
                        "topic_name",
                        "product",
                        "category",
                        "subcategory",
                        "ticket_indices",
                        "summary"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": ["clusters"],
        "additionalProperties": False
    }
