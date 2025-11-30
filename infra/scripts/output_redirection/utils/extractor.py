
from typing import Dict, Any
from pydantic import BaseModel
import subprocess
import json
import os

class Extractor:
      def __init__(self, environment, terraform_dir) -> None:
            self.environment = environment
            self.terraform_dir = terraform_dir
      def _extract_outputs(self):
                  # First, check if terraform outputs are provided via environment variable
                  # This is useful for CI/CD environments where terraform credentials may not be available
                  terraform_outputs_json = os.getenv("TERRAFORM_OUTPUTS_JSON")

                  if terraform_outputs_json:
                        print("Using terraform outputs from TERRAFORM_OUTPUTS_JSON environment variable")
                        print(terraform_outputs_json)
                        raw_outputs = json.loads(terraform_outputs_json)
                  else:
                        print(f"Fetching terraform outputs from terraform directory: {self.terraform_dir}")
                        output = subprocess.run(
                              ["terraform", "output",  "-json"],
                              cwd=self.terraform_dir,
                              check=True,
                              text=True,
                              capture_output=True
                        )
                        raw_outputs = json.loads(output.stdout)

                  flattened_outputs = {
                        key: value["value"]
                        for key, value in raw_outputs.items()
                  }

                  ssh_key_path_env = os.environ.get("SSH_PRIVATE_KEY_PATH")
                  if ssh_key_path_env:
                        print(f"Overriding SSH key path with: {ssh_key_path_env}")
                        flattened_outputs["vm_app_server_ssh_private_key_file_path"] = os.path.expanduser(ssh_key_path_env)

                  validated_outputs = self._filter_terraform_outputs(flattened_outputs)
                  print(f"Validated outputs: {validated_outputs}")
                  return validated_outputs

      def _filter_terraform_outputs(self, outputs: Dict[str, Any]):
            frontend_model, backend_model, ansible_model = self._get_models_per_environment(self.environment)
            filtered_outputs = {
                  "frontend": self._filter_outputs_for_model(outputs, frontend_model),
                  "backend": self._filter_outputs_for_model(outputs, backend_model),
                  "ansible": self._filter_outputs_for_model(outputs, ansible_model),
            }
            return filtered_outputs



      def _get_models_per_environment(self, environment: str):
            from ..models.dev import DevBackendOutputs, DevFrontendOutputs, DevAnsibleOutputs
            from ..models.production import ProductionBackendOutputs, ProductionFrontendOutputs, ProductionAnsibleOutputs
            from ..models.staging import StagingBackendOutputs, StagingFrontendOutputs, StagingAnsibleOutputs

            model_mapping = {
                  "dev": (DevFrontendOutputs, DevBackendOutputs, DevAnsibleOutputs),
                  "staging": (StagingFrontendOutputs, StagingBackendOutputs, StagingAnsibleOutputs),
                  "production": (ProductionFrontendOutputs, ProductionBackendOutputs, ProductionAnsibleOutputs),
            }

            model_class = model_mapping.get(environment)
            if not model_class:
                  raise ValueError(f"No validation model found for environment: {self.environment}")
            return model_class
      def _filter_outputs_for_model(self, outputs: Dict[str, Any], model_class: BaseModel):
            if not model_class:
                  return {}

            model_fields = set(model_class.__fields__.keys())
            filtered = {
                  key.upper(): value for key, value in outputs.items()
                  if key.upper() in model_fields
            }
            return filtered
