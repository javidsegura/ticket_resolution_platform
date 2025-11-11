from typing import Dict
import json

from ai_ticket_platform.core.clients import secrets_manager_client

class SecretsManager():
      def fetch_secret(self, secret_key: str) -> Dict:
            get_secret_value_response = secrets_manager_client.get_secret_value(
                  SecretId=secret_key
            )

            if "SecretString" in get_secret_value_response:
                  secret_value = get_secret_value_response["SecretString"]
                  parsed_secret = json.loads(secret_value)
                  return parsed_secret
            raise ValueError(f"Secret {secret_key} doesnt have a Secret string")