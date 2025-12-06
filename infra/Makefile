.PHONY: help install up down output extract-db-credentials connection-ssh connection-http connection-db connection-port connection-grafana connection-ssh-web-server connection-http-traffic-web-server

SHELL := /bin/bash

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
PYTHON = $(VENV)/bin/python
UV = uv

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

install: ## Initialize Terraform (Local Dev)
	$(UV) venv $(VENV) --python 3.11
	$(UV) pip install -r ./requirements.txt
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform init
	brew install ansible
	$(UV) pip install ansible
	$(PYTHON) -m ansible.galaxy collection install -r ./ansible/dependencies.yml

install-ci-cd: ## CI/CD Installation
	$(UV) venv $(VENV) --python 3.11
	$(UV) pip install -r ./requirements.txt
	$(MAKE) check_enviroment_variables
	ansible-galaxy install -r ./ansible/dependencies.yml



check: ## Apply Terraform configuration
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform plan

terraform-output:
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform output
terraform-output-json: ## Get output in json after `terraform apply`
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

terraform-plan:
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform plan

terraform-validate: ## Validate Terraform configuration (no credentials needed)
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform init -backend=false && terraform validate

terraform-fmt-check: ## Check Terraform formatting (no credentials needed)
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform fmt -check -recursive

terraform-fmt: ## Format Terraform files (no credentials needed)
	$(MAKE) check_enviroment_variables
	cd $(TERRAFORM_ENVIRONMENT_PATH) && terraform fmt -recursive

terraform-fmt-all: ## Format all Terraform files (for pre-commit, no credentials needed)
	@echo "$(YELLOW)Formatting all Terraform files...$(RESET)"
	@for dir in terraform/*/environment/* terraform/*/set-up terraform/*/modules/*; do \
		if [ -d "$$dir" ] && [ -n "$$(find $$dir -name '*.tf' -type f)" ]; then \
			echo "$(BLUE)Formatting $$dir...$(RESET)"; \
			cd $$dir && terraform fmt -recursive && cd - > /dev/null; \
		fi; \
	done
	@echo "$(GREEN)All Terraform files formatted$(RESET)"

sync_backend_env: ## Inject tf outputs into backend dotenv
	@echo "Syncing Terraform outputs to backend .env..."
	$(MAKE) check_enviroment_variables
	mkdir -p ../backend/env_config/synced
	$(PYTHON) -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --backend-dotenv-path $(BASE_BACKEND_ENV_FILE_PATH)

sync_frontend_env:  ## Inject tf outputs into frontend dotenv
	@echo "Syncing Terraform outputs to backend .env..."
	$(MAKE) check_enviroment_variables
	mkdir -p ../frontend/app/env_config/synced
	$(PYTHON) -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --frontend-dotenv-path $(BASE_FRONTEND_ENV_FILE_PATH)


sync_ansible_inventory: ## ## Inject tf outputs into ansible
	@echo "Syncing Terraform outputs to Ansible inventory..."
	$(MAKE) check_enviroment_variables
	mkdir -p ansible/inventory
	$(PYTHON) -m $(SYNC_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --ansible-inventory-path $(ANSIBLE_INVENTORY_FILE_PATH)
sync_envs:
	$(MAKE) sync_backend_env
	$(MAKE) sync_frontend_env
sync_all: ## Syncs tf output in dotenvs (backend and frontend) and ansible
	$(MAKE) sync_envs
	$(MAKE) sync_ansible_inventory

extract-db-credentials: ## Extract credentials from db
	python3 -m scripts.resource_connections.extract_db_credentials \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH)


connection-db: ## SSH tunnel for database (default: local 3307 -> remote 3306)
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection db

connection-ssh-web-server: ## Alias for connection-ssh
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection ssh
connection-http-traffic-web-server: ## Alias for connection-http
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection web-serving

connection-grafana: ## SSH tunnel for Grafana (defaults to port 3000, can override with LOCAL_PORT and REMOTE_PORT)
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection grafana \
	   $(if $(LOCAL_PORT),--local-port $(LOCAL_PORT),) \
	   $(if $(REMOTE_PORT),--remote-port $(REMOTE_PORT),) \
	   $(if $(TARGET_HOST),--target-host $(TARGET_HOST),)

connection-port: ## Generic SSH tunnel for any port (requires LOCAL_PORT and REMOTE_PORT variables, optional TARGET_HOST)
	@if [ -z "$(LOCAL_PORT)" ] || [ -z "$(REMOTE_PORT)" ]; then \
		echo "Error: LOCAL_PORT and REMOTE_PORT must be defined"; \
		echo "Usage: make connection-port LOCAL_PORT=3000 REMOTE_PORT=3000 [TARGET_HOST=hostname]"; \
		exit 1; \
	fi
	python3 -m $(CONNECTION_SCRIPT_PATH) \
	   --environment $(ENVIRONMENT) \
	   --terraform-dir $(TERRAFORM_ENVIRONMENT_PATH) \
	   --type-of-connection port \
	   --local-port $(LOCAL_PORT) \
	   --remote-port $(REMOTE_PORT) \
	   $(if $(TARGET_HOST),--target-host $(TARGET_HOST),)


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
