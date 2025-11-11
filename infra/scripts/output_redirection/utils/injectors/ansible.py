from typing import Dict
from ...templates import ANSIBLE_TEMPLATE_PRODUCTION, ANSIBLE_TEMPLATE_STAGING
from jinja2 import Template

class AnsibleInjector:
      def __init__(self, environment: str) -> None:
            self.environment = environment
      def ansible_injection(self, ansible_outputs: Dict):
            if self.environment == "dev":
                  raise ValueError("No ansible available for env stage")
            elif self.environment == "production":
                  template = Template(ANSIBLE_TEMPLATE_PRODUCTION)
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
