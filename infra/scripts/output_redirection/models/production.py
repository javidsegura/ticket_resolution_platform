from pydantic import BaseModel


class ProductionBackendOutputs(BaseModel):
      # AWS, AZURE
      SECRETS_MANAGER_DB_CREDENTIALS_KEY: str

      # AWS
      S3_MAIN_BUCKET_NAME: str
      RDS_MYSQL_HOST: str # Handle the renaming with a factory for each enviroment in the settings class

      # AZURE
      AZURE_STORAGE_CONTAINER_NAME: str
      AZURE_KEY_VAULT_NAME: str
      MYSQL_HOST: str


class ProductionFrontendOutputs(BaseModel):
      # AWS
      EC2_APP_SERVER_PUBLIC_IP: str

      # AZURE
      VM_APP_SERVER_PUBLIC_IP: str


class ProductionAnsibleOutputs(BaseModel):
      # AWS
      EC2_APP_SERVER_PUBLIC_IP: str
      EC2_APP_SERVER_SSH_USER: str
      EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH: str


      # AZURE
      VM_APP_SERVER_PUBLIC_IP: str
      VM_APP_SERVER_SSH_USER: str
      VM_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH: str
