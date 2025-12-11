import argparse
from typing import Any, Dict
import json
import os
import subprocess

from .utils.models.production import ProdConnectionModelAWS, ProdConnectionModelAzure
from .utils.models.staging import StagingConnectionModel
from .utils.secrets.ssh import get_ssh_key_path

class ConnectionEstabisher():
      """
      REFACTORING TO BE DONE:
            - Create bridge between type of connection and environments
      """
      def __init__(self, environment :str, terraform_dir :str) -> None:
            self.environment = environment
            self.terraform_dir = terraform_dir
            self.cloud_provider = os.getenv("CLOUD_PROVIDER", "AWS").upper()
            if self.environment == "production" and self.cloud_provider not in ["AWS", "AZURE"]:
                  raise ValueError(f"CLOUD_PROVIDER must be 'AWS' or 'AZURE' for production environment. Got: {self.cloud_provider}")
            self.terraform_outputs = self.extract_terraform_outputs()

      def extract_terraform_outputs(self) -> ProdConnectionModelAWS | ProdConnectionModelAzure | StagingConnectionModel:
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
                  if self.cloud_provider == "AWS":
                        model_fields = set(ProdConnectionModelAWS.model_fields.keys())
                  elif self.cloud_provider == "AZURE":
                        model_fields = set(ProdConnectionModelAzure.model_fields.keys())
                  else:
                        raise ValueError(f"Unsupported cloud provider: {self.cloud_provider}")
            elif self.environment == "staging":
                  model_fields = set(StagingConnectionModel.model_fields.keys())
            else:
                  raise ValueError(f"Unsupported environment: {self.environment}")

            filtered = {
                  key.upper(): value["value"] for key, value in raw_outputs.items()
                  if key.upper() in model_fields
            }
            if self.environment == "production":
                  if self.cloud_provider == "AWS":
                        return ProdConnectionModelAWS(**filtered)
                  elif self.cloud_provider == "AZURE":
                        return ProdConnectionModelAzure(**filtered)
            elif self.environment == "staging":
                  return StagingConnectionModel(**filtered)

      def _handle_ssh_connection(self):
            # Fetch SSH key from Secrets Manager (always fresh)
            SSH_PRIVATE_KEY_FILE_PATH = get_ssh_key_path(self.terraform_dir)
            print(f"SSH_PRIVATE_KEY_FILE_PATH: {SSH_PRIVATE_KEY_FILE_PATH}")

            if self.environment == "production":
                  if self.cloud_provider == "AWS":
                        SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                        PUBLIC_IP = self.terraform_outputs.EC2_APP_SERVER_PUBLIC_IP
                  elif self.cloud_provider == "AZURE":
                        SSH_USER = self.terraform_outputs.VM_APP_SERVER_SSH_USER
                        PUBLIC_IP = self.terraform_outputs.VM_APP_SERVER_PUBLIC_IP
                        SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.VM_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH

                  subprocess.call(
                        ["ssh", "-i", f"{SSH_PRIVATE_KEY_FILE_PATH}", f"{SSH_USER}@{PUBLIC_IP}"]
                  )
            elif self.environment == "staging":
                  EC2_APP_SERVER_SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                  EC2_APP_SERVER_PRIVATE_IP = self.terraform_outputs.EC2_APP_SERVER_PRIVATE_IP
                  EC2_BASTION_SERVER_SSH_USER = self.terraform_outputs.EC2_BASTION_SERVER_SSH_USER
                  EC2_BASTION_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_BASTION_SERVER_PUBLIC_IP

                  proxy_command = f"ssh -i {SSH_PRIVATE_KEY_FILE_PATH} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -W %h:%p -q {EC2_BASTION_SERVER_SSH_USER}@{EC2_BASTION_SERVER_PUBLIC_IP}"

                  cmd = [
                        "ssh",
                        "-i", SSH_PRIVATE_KEY_FILE_PATH,
                        "-o", f"ProxyCommand={proxy_command}",
                        f"{EC2_APP_SERVER_SSH_USER}@{EC2_APP_SERVER_PRIVATE_IP}"
                  ]

                  print(f"Command is: {cmd}")
                  subprocess.call(
                        cmd
                  )
            else:
                  raise ValueError("Environment must be production or staging")
      def _handle_port_connection(self, local_port_to_send_from, local_port_to_receive_from, target_host=None, connection_name="port"):
            """
            Create an SSH tunnel to forward a local port to a remote port.

            Args:
                  local_port_to_send_from: Local port to bind to
                  local_port_to_receive_from: Remote port to forward to
                  target_host: Target host (if None, uses app server)
                  connection_name: Name for logging purposes
            """
            # Fetch SSH key from Secrets Manager (always fresh)
            SSH_PRIVATE_KEY_FILE_PATH = get_ssh_key_path(self.terraform_dir)

            if self.environment == "production":
                  if self.cloud_provider == "AWS":
                        SSH_USER = self.terraform_outputs.EC2_APP_SERVER_SSH_USER
                        PUBLIC_IP = self.terraform_outputs.EC2_APP_SERVER_PUBLIC_IP
                  elif self.cloud_provider == "AZURE":
                        SSH_USER = self.terraform_outputs.VM_APP_SERVER_SSH_USER
                        PUBLIC_IP = self.terraform_outputs.VM_APP_SERVER_PUBLIC_IP
                        SSH_PRIVATE_KEY_FILE_PATH = self.terraform_outputs.VM_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH

                  # Use provided target_host or default to app server public IP
                  remote_host = target_host if target_host else "localhost"

                  cmd = ["ssh", "-i", f"{SSH_PRIVATE_KEY_FILE_PATH}", "-N", "-L",
                         f"{local_port_to_send_from}:{remote_host}:{local_port_to_receive_from}",
                         f"{SSH_USER}@{PUBLIC_IP}"]

                  print(f"Connection started for {connection_name} at localhost:{local_port_to_send_from} -> {remote_host}:{local_port_to_receive_from}")
                  subprocess.call(cmd)
            elif self.environment == "staging":
                  EC2_BASTION_SERVER_SSH_USER = self.terraform_outputs.EC2_BASTION_SERVER_SSH_USER
                  EC2_BASTION_SERVER_PUBLIC_IP = self.terraform_outputs.EC2_BASTION_SERVER_PUBLIC_IP
                  EC2_APP_SERVER_PRIVATE_IP = self.terraform_outputs.EC2_APP_SERVER_PRIVATE_IP

                  # Use provided target_host or default to app server private IP
                  remote_host = target_host if target_host else EC2_APP_SERVER_PRIVATE_IP

                  cmd = ["ssh", "-i", f"{SSH_PRIVATE_KEY_FILE_PATH}", "-N", "-L",
                         f"{local_port_to_send_from}:{remote_host}:{local_port_to_receive_from}",
                         f"{EC2_BASTION_SERVER_SSH_USER}@{EC2_BASTION_SERVER_PUBLIC_IP}"]

                  print(f"Connection started for {connection_name} at localhost:{local_port_to_send_from} -> {remote_host}:{local_port_to_receive_from}")
                  subprocess.call(cmd)
            else:
                  raise ValueError("Environment must be production or staging")
      def _handle_web_serving_connection(self):
            if self.environment == "production":
                  raise ValueError("Web served for production is served by accessing the web server public ip. Theres no set-up to be done \
                        for the connection")
            elif self.environment == "staging":
                  self._handle_port_connection(
                        local_port_to_send_from=8080,
                        local_port_to_receive_from=80,
                        connection_name="web serving"
                  )
            else:
                  raise ValueError("Environment must be production or staging")
      def _handle_db_connection(self):
            if self.environment == "production":
                  if self.cloud_provider == "AWS":
                        MYSQL_HOST = self.terraform_outputs.RDS_MYSQL_HOST
                  elif self.cloud_provider == "AZURE":
                        MYSQL_HOST = self.terraform_outputs.MYSQL_HOST

                  self._handle_port_connection(
                        local_port_to_send_from=3307,
                        local_port_to_receive_from=3306,
                        target_host=MYSQL_HOST,
                        connection_name="database"
                  )
            elif self.environment == "staging":
                  RDS_MYSQL_HOST = self.terraform_outputs.RDS_MYSQL_HOST
                  self._handle_port_connection(
                        local_port_to_send_from=3307,
                        local_port_to_receive_from=3306,
                        target_host=RDS_MYSQL_HOST,
                        connection_name="database"
                  )
            else:
                  raise ValueError("Environment must be production or staging")

      def connect(self, type_of_connection: str, local_port: int = None, remote_port: int = None, target_host: str = None):
            """
            Establish a connection based on the type specified.

            Args:
                  type_of_connection: Type of connection ("ssh", "web-serving", "db", "port", "grafana")
                  local_port: Local port to bind to (for port/grafana connections)
                  remote_port: Remote port to forward to (for port/grafana connections)
                  target_host: Target host (optional, for port connections)
            """
            if type_of_connection == "ssh":
                  self._handle_ssh_connection()
            elif type_of_connection == "web-serving":
                  self._handle_web_serving_connection()
            elif type_of_connection == "db":
                  self._handle_db_connection()
            elif type_of_connection == "port":
                  if local_port is None or remote_port is None:
                        raise ValueError("local_port and remote_port are required for 'port' connection type")
                  self._handle_port_connection(
                        local_port_to_send_from=local_port,
                        local_port_to_receive_from=remote_port,
                        target_host=target_host,
                        connection_name="port forwarding"
                  )
            elif type_of_connection == "grafana":
                  self._handle_port_connection(
                        local_port_to_send_from=local_port if local_port else 3000,
                        local_port_to_receive_from=remote_port if remote_port else 3000,
                        target_host=target_host,
                        connection_name="Grafana"
                  )
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
                         help="Type of connection to establish",
                         required=True,
                         choices=["ssh", "db", "web-serving", "port", "grafana"])
      parser.add_argument("--local-port",
                         help="Local port to bind to (required for 'port' and 'grafana' connection types)",
                         type=int,
                         default=None)
      parser.add_argument("--remote-port",
                         help="Remote port to forward to (required for 'port' and 'grafana' connection types)",
                         type=int,
                         default=None)
      parser.add_argument("--target-host",
                         help="Target host for port forwarding (optional, defaults to app server)",
                         type=str,
                         default=None)

      args = parser.parse_args()
      connector = ConnectionEstabisher(environment=args.environment,
                                       terraform_dir=args.terraform_dir)
      connector.connect(
            type_of_connection=args.type_of_connection,
            local_port=args.local_port,
            remote_port=args.remote_port,
            target_host=args.target_host
      )
