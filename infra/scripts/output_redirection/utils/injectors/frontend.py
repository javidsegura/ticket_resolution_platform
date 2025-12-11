

import os
from typing import Any, Dict

from pydantic import BaseModel
from ...templates import ENV_TEMPLATE
from jinja2 import Template

class FrontendInjector:
      def __init__(self, environment) -> None:
            self.environment = environment

      def _extract_server_ip(self, ansible_outputs: dict):
            cloud_provider = os.getenv("CLOUD_PROVIDER").lower()
            if cloud_provider == "aws":
                  return ansible_outputs.get("EC2_APP_SERVER_PUBLIC_IP")
            elif cloud_provider == "azure":
                  return ansible_outputs.get("VM_APP_SERVER_PUBLIC_IP")

      def _resolve_base_url(self, ansible_outputs: dict):
            server_ip = self._extract_server_ip(ansible_outputs)
            if self.environment == "dev":
                  return {"VITE_BASE_URL": "http://localhost/api/"}
            elif self.environment == "staging":
                  return {"VITE_BASE_URL": "http://localhost:8080/api/"}
            elif self.environment == "production":
                  return {"VITE_BASE_URL": f"http://{server_ip}/api/"}
            else:
                  raise ValueError(f"Environment can only be dev, production or staging. Currently you have: '{self.environment}'")

      def frontend_dotenv_injection(self, frontend_outputs: str):
            template = Template(ENV_TEMPLATE)
            vite_base_app_url = self._resolve_base_url(frontend_outputs)

            sycned_content = template.render(outputs=vite_base_app_url)
            return sycned_content
