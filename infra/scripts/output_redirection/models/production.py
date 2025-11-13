from pydantic import BaseModel


class ProductionBackendOutputs(BaseModel):
      S3_MAIN_BUCKET_NAME: str
      SECRETS_MANAGER_DB_CREDENTIALS_KEY: str
      RDS_MYSQL_HOST: str # Handle the renaming with a factory for each enviroment in the settings class


class ProductionFrontendOutputs(BaseModel):
      EC2_APP_SERVER_PUBLIC_IP: str

class ProductionAnsibleOutputs(BaseModel):
      EC2_APP_SERVER_PUBLIC_IP: str
      EC2_APP_SERVER_SSH_USER: str
      EC2_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH: str
