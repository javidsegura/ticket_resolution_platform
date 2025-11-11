import argparse
import boto3
import json
import subprocess

def extract_terraform_outputs(terraform_dir: str):
      try:
            output = subprocess.run(
                  ["terraform", "output", "-json"],
                  cwd=terraform_dir,
                  check=True,
                  text=True,
                  capture_output=True
            )
            raw_outputs = json.loads(output.stdout)
            secret_key = raw_outputs["rds_db_credentials_key"]["value"]
            return secret_key
      except:
            raise 


def fetch_secret(secret_key:str, region_name: str):
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
                  return secret_value
      return None

if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Extract credentials from AWS secrets manager")
      parser.add_argument("--terraform-dir", help="Directory of tf --where terraform output -json will be executed", required=True)
      parser.add_argument("--region-name", help="AWS region name", required=True)

      args = parser.parse_args()
      secret_key = extract_terraform_outputs(args.terraform_dir)
      print(fetch_secret(secret_key, region_name=args.region_name))

