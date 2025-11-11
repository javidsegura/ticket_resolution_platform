import argparse
from typing import Any, Dict
import boto3
import json
import os
import subprocess

from .utils import ProdConnectionModel, StagingConnectionModel

class ConnectionEstabisher():
      """
      REFACTORING TO BE DONE: 
            - Create bridge between type of connection and environments 
      """
      def __init__(self, environment :str, terraform_dir :str) -> None:
            self.environment = environment
            self.terraform_dir = terraform_dir
            self.terraform_outputs = self.extract_terraform_outputs()

      def extract_terraform_outputs(self) -> ProdConnectionModel | StagingConnectionModel:
            try:
                  # Extract raw outputs
                  output = subprocess.run(
                        ["terraform", "output", "-json"],
                        cwd=self.terraform_dir,
                        check=True,
                        text=True,
                        capture_output=True
                  )
                  raw_outputs = json.loads(output.stdout)
                  # Filter outputs to pydantic model
                  print(f"raw_outputs: {raw_outputs}")
                  return self._filter_outputs_for_model(raw_outputs)
            except:
                  raise 
      def _filter_outputs_for_model(self, raw_outputs: Dict[str, Any]):
            if self.environment == "production":
                  model_fields = set(ProdConnectionModel.model_fields.keys())
            elif self.environment == "staging":
                  model_fields = set(StagingConnectionModel.model_fields.keys())
            filtered = {
                  key.upper(): value["value"] for key, value in raw_outputs.items()
                  if key.upper() in model_fields
            }
            if self.environment == "production":
                  return ProdConnectionModel(**filtered)
            elif self.environment == "staging":
                  return StagingConnectionModel(**filtered)

      def _handle_ssh_connection(self):
            if self.environment == "production":
                  EC2_APP_SERVER_SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                  EC2_APP_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_APP_SERVER_PUBLIC_IP
                  EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH

                  subprocess.call(
                        ["ssh", "-i", f"{EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH}", f"{EC2_APP_SERVER_SSH_USER}@{EC2_APP_SERVER_PUBLIC_IP}"]
                  )
            elif self.environment == "staging":
                  EC2_APP_SERVER_SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                  EC2_APP_SERVER_PRIVATE_IP = self.terraform_outputs.EC2_APP_SERVER_PRIVATE_IP
                  EC2_BASTION_SERVER_SSH_USER = self.terraform_outputs.EC2_BASTION_SERVER_SSH_USER
                  EC2_BASTION_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_BASTION_SERVER_PUBLIC_IP
                  EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH
            
                  proxy_command = f"ssh -i {EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -W %h:%p -q {EC2_BASTION_SERVER_SSH_USER}@{EC2_BASTION_SERVER_PUBLIC_IP}"
        
                  cmd = [
                        "ssh",
                        "-i", EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH,
                        "-o", f"ProxyCommand={proxy_command}",
                        f"{EC2_APP_SERVER_SSH_USER}@{EC2_APP_SERVER_PRIVATE_IP}"
                  ]
                  
                  print(f"Command is: {cmd}")
                  subprocess.call(
                        cmd
                  )
            else:
                  raise ValueError("Environment must be production or staging")
      def _handle_web_serving_connection(self):
            if self.environment == "production":
                  raise ValueError("Web served for production is served by accessing the web server public ip. Theres no set-up to be done \
                        for the connection")
            elif self.environment == "staging":
                  EC2_BASTION_SERVER_SSH_USER = self.terraform_outputs.EC2_BASTION_SERVER_SSH_USER
                  EC2_BASTION_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_BASTION_SERVER_PUBLIC_IP
                  EC2_APP_SERVER_PRIVATE_IP = self.terraform_outputs.EC2_APP_SERVER_PRIVATE_IP
                  EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH
                  local_port_to_send_from = 8080
                  local_port_to_receive_from = 80

                  cmd = ["ssh", "-i", f"{EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH}", "-N", "-L",
                         f"{local_port_to_send_from}:{EC2_APP_SERVER_PRIVATE_IP}:{local_port_to_receive_from}",
                         f"{EC2_BASTION_SERVER_SSH_USER}@{EC2_BASTION_SERVER_PUBLIC_IP}"]

                  print(f"Conection started for web serving, access: http://localhost:{local_port_to_send_from}: ")
                  subprocess.call(
                        cmd
                  )
            else:
                  raise ValueError("Environment must be production or staging")
      def _handle_db_connection(self):
            if self.environment == "production":
                  EC2_APP_SERVER_SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                  EC2_APP_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_APP_SERVER_PUBLIC_IP
                  RDS_MYSQL_HOST = self.terraform_outputs.RDS_MYSQL_HOST
                  EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH
                  local_port_to_send_from = 3307
                  local_port_to_receive_from = 3306

                  cmd = ["ssh", "-i", f"{EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH}", "-N", "-L",
                         f"{local_port_to_send_from}:{RDS_MYSQL_HOST}:{local_port_to_receive_from}",
                         f"{EC2_APP_SERVER_SSH_USER}@{EC2_APP_SERVER_PUBLIC_IP}"]

                  print(f"Conection started for db at port {local_port_to_send_from}: ")
                  subprocess.call(
                        cmd
                  )
            elif self.environment == "staging":
                  EC2_BASTION_SERVER_SSH_USER = self.terraform_outputs.EC2_BASTION_SERVER_SSH_USER
                  EC2_BASTION_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_BASTION_SERVER_PUBLIC_IP
                  RDS_MYSQL_HOST = self.terraform_outputs.RDS_MYSQL_HOST
                  EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH
                  local_port_to_send_from = 3307
                  local_port_to_receive_from = 3306
                  
                  cmd = ["ssh", "-i", f"{EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH}", "-N", "-L",
                         f"{local_port_to_send_from}:{RDS_MYSQL_HOST}:{local_port_to_receive_from}",
                         f"{EC2_BASTION_SERVER_SSH_USER}@{EC2_BASTION_SERVER_PUBLIC_IP}"]
                  print(f"Conection started: ")
                  subprocess.call(
                        cmd
                  )
            else:
                  raise ValueError("Environment must be production or staging")
            
      def connect(self, type_of_connection: str):
            if type_of_connection == "ssh":
                  self._handle_ssh_connection()
            elif type_of_connection == "web-serving":
                  self._handle_web_serving_connection()
            elif type_of_connection == "db":
                  self._handle_db_connection()
            else:
                  raise ValueError(f"No type of connection registered for: {type_of_connection}")




if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Extract credentials from AWS secrets manager")
      parser.add_argument("--environment",
                         help="Determine environment of execution", 
                         required=True,
                         choices=["dev", "staging", "production"])
      parser.add_argument("--terraform-dir", help="Directory of tf --where terraform output -json will be executed", required=True)
      parser.add_argument("--type-of-connection",
                         help="AWS region name",
                         required=True, 
                         choices=["ssh", "db", "web-serving"])

      args = parser.parse_args()
      connector = ConnectionEstabisher(environment=args.environment,
                                       terraform_dir=args.terraform_dir)
      connector.connect(type_of_connection=args.type_of_connection)

