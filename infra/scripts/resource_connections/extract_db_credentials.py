import argparse
import boto3
import json
import subprocess
import os
from typing import Dict, Any

def extract_terraform_outputs(terraform_dir: str, cloud_provider: str) -> Dict[str, str]:
      """
      Extract terraform outputs based on cloud provider.
      Returns a dictionary with the necessary information to fetch secrets.
      """
      try:
            output = subprocess.run(
                  ["terraform", "output", "-json"],
                  cwd=terraform_dir,
                  check=True,
                  text=True,
                  capture_output=True
            )
            raw_outputs = json.loads(output.stdout)

            if cloud_provider.lower() == "aws":
                  secret_key = raw_outputs["secrets_manager_db_credentials_key"]["value"]
                  region_name = raw_outputs["aws_main_region"]["value"]
                  return {"secret_key": secret_key, "region_name": region_name, "output_type": "aws"}
            elif cloud_provider.lower() == "azure":
                  secret_name = raw_outputs["key_vault_db_secret_name"]["value"]
                  vault_name = raw_outputs["key_vault_name"]["value"]
                  return {"secret_name": secret_name, "vault_name": vault_name, "output_type": "azure"}
            else:
                  raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
      except Exception as e:
            raise Exception(f"Failed to extract terraform outputs: {str(e)}")


def fetch_secret_aws(secret_key: str, region_name: str) -> Dict[str, Any]:
      """Fetch secret from AWS Secrets Manager."""
      secrets_manager_client = boto3.client("secretsmanager", region_name=region_name)
      get_secret_value_response = secrets_manager_client.get_secret_value(
            SecretId=secret_key
      )

      if "SecretString" in get_secret_value_response:
            secret_value = get_secret_value_response["SecretString"]
            try:
                  parsed_secret = json.loads(secret_value)
                  return parsed_secret
            except json.JSONDecodeError:
                  return {"value": secret_value}
      return None


def fetch_secret_azure(vault_name: str, secret_name: str) -> Dict[str, Any]:
      """Fetch secret from Azure Key Vault."""
      try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
      except ImportError:
            raise ImportError(
                  "Azure Key Vault libraries not installed. "
                  "Install with: pip install azure-keyvault-secrets azure-identity"
            )

      # Create Key Vault URL
      vault_url = f"https://{vault_name}.vault.azure.net"

      # Authenticate using DefaultAzureCredential (works with managed identity, CLI, env vars, etc.)
      credential = DefaultAzureCredential()

      # Create SecretClient
      secret_client = SecretClient(vault_url=vault_url, credential=credential)

      # Get secret value
      secret = secret_client.get_secret(secret_name)

      if secret.value:
            try:
                  # Try to parse as JSON (credentials are stored as JSON in the terraform module)
                  parsed_secret = json.loads(secret.value)
                  return parsed_secret
            except json.JSONDecodeError:
                  # If not JSON, return as plain value
                  return {"value": secret.value}

      return None


if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Extract credentials from cloud secrets manager")
      parser.add_argument("--terraform-dir", help="Directory where terraform output -json will be executed", required=True)
      parser.add_argument("--region-name", help="AWS region name (optional, will be extracted from terraform outputs if not provided)", required=False)

      args = parser.parse_args()

      # Get cloud provider from environment variable
      cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()

      if cloud_provider not in ["aws", "azure"]:
            raise ValueError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}. Must be 'aws' or 'azure'")

      # Extract terraform outputs
      outputs = extract_terraform_outputs(args.terraform_dir, cloud_provider)

      # Fetch secret based on provider
      if cloud_provider == "aws":
            # Use region from terraform outputs (preferred) or fall back to command line arg
            region_name = outputs.get("region_name") or args.region_name
            if not region_name:
                  raise ValueError("AWS region name is required. Either provide --region-name or ensure 'aws_main_region' is in terraform outputs")
            secret = fetch_secret_aws(outputs["secret_key"], region_name)
      else:  # azure
            secret = fetch_secret_azure(outputs["vault_name"], outputs["secret_name"])

      # Output as JSON
      print(json.dumps(secret, indent=2))
