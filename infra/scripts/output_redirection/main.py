"""
Improvments for this script:
      - Add modularity by implementing a factory design pattern
"""

from multiprocessing import Value
import os
import argparse
from typing import Any, Dict, Tuple
import json

from jinja2 import Template
from pydantic import BaseModel
import shutil
from .utils import Extractor, BackendInjector, FrontendInjector, AnsibleInjector

class VariableInjector():
      """
      This class provides the methods for injecting terraform outputs in the corresponding Jinja2 templates
      """

      def __init__(self, environment: str, terraform_dir: str) -> None:
            self.environment = environment
            self.terraform_dir = terraform_dir
            self.terraform_outputs : Dict(Dict, Dict, Dict) = Extractor(environment=self.environment, terraform_dir=self.terraform_dir)._extract_outputs()
            self.backend_injector = BackendInjector(environment=self.environment)
            self.frontend_injector = FrontendInjector(environment=self.environment)
            self.ansible_injector = AnsibleInjector(environment=self.environment)


      def _write_injection(self, file_name: str, content: str, file_mode: str = "w"):
            """
            Args:
                  file_name (str):  top-level relative
            """
            if file_mode == "a":
                  if not os.path.exists(file_name):
                        raise ValueError(f"Path {file_name} doesnt exist. Cant append")
            with open(file=f"{file_name}", mode=file_mode) as f:
                  f.write(content)

      def _create_copy_of_base_file(self, base_env_path: str):
            if not os.path.exists(base_env_path):
                  raise Exception(f"base env path {base_env_path} doesnt exist")
            synced_file_path = base_env_path.replace("/base/", "/synced/")
            shutil.copy(base_env_path, synced_file_path)
            return synced_file_path

      def backend_dotenv_injection(self, base_env_path: str):
            synced_content = self.backend_injector.backend_dotenv_injection(backend_outputs=self.terraform_outputs.get("backend"))
            synced_file_path = self._create_copy_of_base_file(base_env_path=base_env_path)
            self._write_injection(
                                    file_name=synced_file_path,
                                    content=synced_content, file_mode="a")


      def frontend_dotenv_injection(self, base_env_path: str):
            synced_content = self.frontend_injector.frontend_dotenv_injection(self.terraform_outputs.get("frontend"))
            synced_file_path = self._create_copy_of_base_file(base_env_path=base_env_path)
            self._write_injection(file_name=synced_file_path,
                                    content=synced_content,
                                    file_mode="a")

      def ansible_injection(self, inventory_path: str):
            if self.environment == "dev":
                  raise ValueError("No ansible available for env stage")
            elif self.environment == "production" or self.environment == "staging":
                  synced_content = self.ansible_injector.ansible_injection(self.terraform_outputs.get("ansible"))
                  self._write_injection(file_name=inventory_path,
                                    content=synced_content,
                                    file_mode="w")
            else:
                  raise ValueError(f"Environment can only be dev, production or staging. Currently you have: '{self.environment}'")







if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Generate configuration files based on terraform outputs")
      parser.add_argument("--environment",
                        help="Takes on [staging, dev, prod]",
                        required=True,
                        choices=["dev", "staging", "production"])
      parser.add_argument("--terraform-dir", help="Directory of tf --where terraform output -json will be executed", required=True)
      parser.add_argument("--backend-dotenv-path", help="Type: str. Needs tp be the path to the base env. \
                                                Will be used to access the create a copy of base_env with appended template stuff ")
      parser.add_argument("--frontend-dotenv-path", help="Type: str. Path for where to write to the frontend. \
                                                Will be used to access the create a copy of base_env with appended template stuff ")
      parser.add_argument("--ansible-inventory-path", help="Type: str. Path to write the rendered ansible template ")

      args = parser.parse_args()
      injector = VariableInjector(environment=args.environment, terraform_dir=args.terraform_dir)

      if args.backend_dotenv_path:
            injector.backend_dotenv_injection(base_env_path=args.backend_dotenv_path)

      if args.frontend_dotenv_path:
            injector.frontend_dotenv_injection(base_env_path=args.frontend_dotenv_path)

      if args.ansible_inventory_path:
            injector.ansible_injection(inventory_path=args.ansible_inventory_path)
