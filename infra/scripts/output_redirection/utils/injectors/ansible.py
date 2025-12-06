from typing import Dict
from ...templates import ANSIBLE_TEMPLATE_PRODUCTION_AWS, ANSIBLE_TEMPLATE_PRODUCTION_AZURE, ANSIBLE_TEMPLATE_STAGING
from jinja2 import Template
import os

class AnsibleInjector:
      def __init__(self, environment: str) -> None:
            self.environment = environment
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
                  print(f"Ansible output: {ansible_outputs}")
                  synced_content = template.render(outputs=ansible_outputs)
                  return synced_content
            elif self.environment == "staging":
                  template = Template(ANSIBLE_TEMPLATE_STAGING)
                  print(f"Ansible output: {ansible_outputs}")
                  synced_content = template.render(outputs=ansible_outputs)
                  return synced_content
            else:
                  raise ValueError(f"Environment can only be dev, production or staging. Currently you have: '{self.environment}'")
