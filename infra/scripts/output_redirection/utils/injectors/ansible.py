from typing import Dict
from ...templates import ANSIBLE_TEMPLATE_PRODUCTION_AWS, ANSIBLE_TEMPLATE_PRODUCTION_AZURE, ANSIBLE_TEMPLATE_STAGING
from jinja2 import Template
import os

# Import existing SSH key fetcher to avoid redundancy
from ....resource_connections.utils.secrets.ssh import fetch_ssh_key_from_secrets_manager, write_ssh_key_to_file


class AnsibleInjector:
      def __init__(self, environment: str) -> None:
            self.environment = environment

      def _fetch_and_cache_ssh_key(self, secret_name: str) -> str:
            """Fetch SSH key using existing fetch_ssh_key module."""
            cache_dir = os.path.expanduser("~/.ssh")

            # Determine key file path based on environment
            if self.environment == "production":
                  key_file = os.path.join(cache_dir, "aws_production_key.pem")
            elif self.environment == "staging":
                  key_file = os.path.join(cache_dir, "aws_staging_key.pem")
            else:
                  key_file = os.path.join(cache_dir, "aws_key.pem")

            # Check if key already cached
            if os.path.exists(key_file):
                  print(f"Using cached SSH key: {key_file}")
                  return key_file

            # Fetch from Secrets Manager using existing function
            print(f"Fetching SSH key from Secrets Manager: {secret_name}")
            key_content = fetch_ssh_key_from_secrets_manager(secret_name)
            write_ssh_key_to_file(key_content, key_file)
            print(f"SSH key cached at: {key_file}")

            return key_file

      def _extract_prod_template(self):
            cloud_provider = os.getenv("CLOUD_PROVIDER").lower()
            if cloud_provider == "aws":
                  return ANSIBLE_TEMPLATE_PRODUCTION_AWS
            elif cloud_provider == "azure":
                  return ANSIBLE_TEMPLATE_PRODUCTION_AZURE

      def ansible_injection(self, ansible_outputs: Dict):
            template_schema = self._extract_prod_template()
            template = Template(template_schema)

            if self.environment == "dev":
                  raise ValueError("No ansible available for env stage")
            elif self.environment == "production":
                  cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()

                  # For AWS, fetch SSH key from Secrets Manager
                  if cloud_provider == "aws" and "SSH_KEY_SECRET_NAME" in ansible_outputs:
                        ssh_key_path = self._fetch_and_cache_ssh_key(
                              ansible_outputs["SSH_KEY_SECRET_NAME"]
                        )
                        ansible_outputs["SSH_KEY_FILE_PATH"] = ssh_key_path

                  print(f"Ansible output: {ansible_outputs}")
                  synced_content = template.render(outputs=ansible_outputs)
                  return synced_content
            elif self.environment == "staging":
                  template = Template(ANSIBLE_TEMPLATE_STAGING)
                  cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()

                  # For AWS staging, fetch SSH key from Secrets Manager
                  if cloud_provider == "aws" and "SSH_KEY_SECRET_NAME" in ansible_outputs:
                        ssh_key_path = self._fetch_and_cache_ssh_key(
                              ansible_outputs["SSH_KEY_SECRET_NAME"]
                        )
                        ansible_outputs["SSH_KEY_FILE_PATH"] = ssh_key_path

                  print(f"Ansible output: {ansible_outputs}")
                  synced_content = template.render(outputs=ansible_outputs)
                  return synced_content
            else:
                  raise ValueError(f"Environment can only be dev, production or staging. Currently you have: '{self.environment}'")
