"""
Fetch SSH private key from AWS Secrets Manager.
"""
import boto3
import json
import os
import subprocess
import sys
from pathlib import Path


def get_secret_name_from_terraform(terraform_dir: str) -> str:
    """Extract SSH key secret name from Terraform outputs."""
    try:
        output = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=terraform_dir,
            check=True,
            text=True,
            capture_output=True
        )
        outputs = json.loads(output.stdout)
        print(f"Outputs: {outputs}")
        return outputs.get("ssh_key_secret_name", {}).get("value")
    except subprocess.CalledProcessError as e:
        print(f"Error getting Terraform outputs: {e}", file=sys.stderr)
        raise
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing Terraform outputs: {e}", file=sys.stderr)
        raise


def fetch_ssh_key_from_secrets_manager(secret_name: str, region: str = "us-east-1") -> str:
    """Fetch SSH private key from AWS Secrets Manager using boto3 SDK."""
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)

        if "SecretString" in response:
            return response["SecretString"]
        else:
            raise ValueError(f"Secret {secret_name} does not contain SecretString")
    except Exception as e:
        print(f"Error fetching secret from AWS Secrets Manager: {e}", file=sys.stderr)
        raise


def write_ssh_key_to_file(key_content: str, file_path: str) -> None:
    """
    Write SSH key to file with proper permissions.

    Args:
        key_content: SSH private key content
        file_path: Full path where to write (e.g., ~/.ssh/aws_production_key.pem)
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(key_content)
    os.chmod(file_path, 0o600)


def get_ssh_key_path(terraform_dir: str, cache_dir: str = None) -> str:
    """
    Get path to SSH key, always fetching fresh from Secrets Manager.

    Args:
        terraform_dir: Path to Terraform directory
        cache_dir: Directory to write the key (default: ~/.ssh)

    Returns:
        Path to SSH private key file
    """
    print(f"Fetching SSH key from Secrets Manager...")
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.ssh")

    # Determine environment from terraform_dir
    if "production" in terraform_dir:
        key_file = os.path.join(cache_dir, "aws_production_key.pem")
    elif "staging" in terraform_dir:
        key_file = os.path.join(cache_dir, "aws_staging_key.pem")
    else:
        key_file = os.path.join(cache_dir, "aws_key.pem")

    # Always fetch fresh key from Secrets Manager
    secret_name = get_secret_name_from_terraform(terraform_dir)

    if not secret_name:
        raise ValueError("Could not determine SSH key secret name from Terraform outputs")

    key_content = fetch_ssh_key_from_secrets_manager(secret_name)
    write_ssh_key_to_file(key_content, key_file)
    print(f"SSH key written to: {key_file}")

    return key_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch SSH key from AWS Secrets Manager")
    parser.add_argument("--terraform-dir", required=True, help="Path to Terraform directory")
    parser.add_argument("--output-file", help="Output file path (default: ~/.ssh/aws_key.pem)")

    args = parser.parse_args()

    key_path = get_ssh_key_path(
        terraform_dir=args.terraform_dir,
        cache_dir=os.path.dirname(args.output_file) if args.output_file else None
    )

    print(key_path)
