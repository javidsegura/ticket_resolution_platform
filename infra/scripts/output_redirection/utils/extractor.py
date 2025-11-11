
from typing import Dict, Any
from pydantic import BaseModel
import subprocess
import json

class Extractor:
      def __init__(self, environment, terraform_dir) -> None:
            self.environment = environment
            self.terraform_dir = terraform_dir
      def _extract_outputs(self):
                  output = subprocess.run(
                        ["terraform", "output",  "-json"],
                        cwd=self.terraform_dir,
                        check=True,
                        text=True,
                        capture_output=True
                  )
                  # raw_outputs = {
                  #       "EC2_PRIVATE_SERVER_INSTANCE_ID": 
                  #       {
                  #             "value": "i-1234567890abcdef0"
                  #       },
                  #       "AWS_MAIN_REGION": 
                  #       {
                  #             "value": "us-east-1"
                  #       },
                  #       "S3_MAIN_BUCKET_NAME": 
                  #       {
                  #             "value": "great-bucket"
                  #       },
                  #       "EC2_APP_SERVER_PUBLIC_IP": 
                  #       {
                  #             "value": "12.323.12"
                  #       },
                  #       "RDS_DB_CREDENTIALS_KEY": 
                  #       {
                  #             "value": "a great key"
                  #       },
                  #       "RDS_MYSQL_HOST": 
                  #       {
                  #             "value": "aws.host.com"
                  #       },
                  # }

                  raw_outputs =  json.loads(output.stdout)
                  flattened_outputs = {
                        key: value["value"]
                        for key, value in raw_outputs.items()
                  }
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