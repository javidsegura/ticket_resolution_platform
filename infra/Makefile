.PHONY: help install up down output extract-db-credentials

# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RESET = \033[0m

.DEFAULT_GOAL := help

# VENV
VENV = ./.venv
VENV_ACTIVATE = source $(VENV)/bin/activate

# DOTENVS
BASE_BACKEND_ENV_FILE_PATH = ../backend/env_config/base/.env.$(ENVIRONMENT)
BASE_FRONTEND_ENV_FILE_PATH = ../frontend/app/env_config/base/.env.$(ENVIRONMENT)
ANSIBLE_INVENTORY_FILE_PATH = ./ansible/inventory/$(ENVIRONMENT).ini

# GENERAL PATHS
TERRAFORM_ENVIRONMENT_PATH=terraform/$(CLOUD_PROVIDER)/environment/$(ENVIRONMENT)
TERRAFORM_SET_UP_PATH=terraform/$(CLOUD_PROVIDER)/set-up

# SCRIPTS
SYNC_SCRIPT_PATH = scripts.output_redirection.main
CONNECTION_SCRIPT_PATH = scripts.resource_connections.create_connection
AWS_SECRETS_MANAGER_REGION=us-east-1

help: ## Show this help message
	@echo "$(BLUE)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)


start-remote-state: ## Starts remote state for terraform (S3)
	cd $(TERRAFORM_SET_UP_PATH) && terraform init && terraform apply 
destroy-remote-state: ## Stops remote state for terraform (S3)
	cd $(TERRAFORM_SET_UP_PATH) && terraform destroy

install: ## Initialize Terraform
	python3.11 -m venv $(VENV)
	pip3 install -r ./requirements.txt
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform init
	brew install ansible
	$(VENV_ACTIVATE) && pip install boto3 botocore
	$(VENV_ACTIVATE) && ansible-galaxy install -r ./ansible/dependencies.yml



check: ## Apply Terraform configuration
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform plan

terraform-output:
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform output 
terraform-output-json:
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform output -json

terraform-apply: ## Apply Terraform configuration
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform apply

terraform-stop: ## Apply Terraform configuration
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform destroy


ansible-ping: ## Check ansible connection is up
	$(MAKE) check_enviroment_variables
	$(VENV_ACTIVATE) && ANSIBLE_CONFIG=./ansible/ansible.cfg ansible all -m ping -i ./ansible/inventory/$(ENVIRONMENT).ini -vvv

ansible-start: ## Runs ansible playbook
	$(VENV_ACTIVATE) && ANSIBLE_CONFIG=./ansible/ansible.cfg ansible-playbook ./ansible/playbook/multi-container.yml -i ./ansible/inventory/$(ENVIRONMENT).ini -e "stage_environment=$(ENVIRONMENT)"

terraform-check:
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform plan

sync_backend_env: ## Inject tf outputs into backend dotenv
	@echo "Syncing Terraform outputs to backend .env..."
	$(MAKE) check_enviroment_variables
	python3 -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --backend-dotenv-path $(BASE_BACKEND_ENV_FILE_PATH)

sync_frontend_env:  ## Inject tf outputs into frontend dotenv
	@echo "Syncing Terraform outputs to backend .env..."
	$(MAKE) check_enviroment_variables
	python3 -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --frontend-dotenv-path $(BASE_FRONTEND_ENV_FILE_PATH)


sync_ansible_inventory: ## ## Inject tf outputs into ansible
	@echo "Syncing Terraform outputs to Ansible inventory..."
	$(MAKE) check_enviroment_variables
	python3 -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --ansible-inventory-path $(ANSIBLE_INVENTORY_FILE_PATH)
sync_envs: 
	$(MAKE) sync_backend_env
	$(MAKE) sync_frontend_env
sync_all: ## Syncs tf output in dotenvs (backend and frontend) and ansible
	$(MAKE) sync_envs
	$(MAKE) sync_ansible_inventory

extract-db-credentials:
	python3 -m scripts.resource_connections.extract_db_credentials \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --region-name $(AWS_SECRETS_MANAGER_REGION)

connection-ssh-web-server: ## Send TCP traffic to port 22 in remote host 
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection ssh
connection-http-traffic-web-server: ## SSH tunnel between local HTTP port and instance HTTP port
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection web-serving
connection-db: ## SSH tunnel between local MySQL port and instance MySQL port
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection db

check_enviroment_variables:
	@if [ -z "$$ENVIRONMENT" ]; then \
		echo "Error: ENVIRONMENT must be defined"; \
		exit 1; \
	fi
	@if [ -z "$$CLOUD_PROVIDER" ]; then \
		echo "Error: ENVIRONMENT must be defined"; \
		exit 1; \
	fi
	echo "Environment is: $(ENVIRONMENT)"