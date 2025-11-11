from pydantic import BaseModel


class StagingBackendOutputs(BaseModel):
      S3_MAIN_BUCKET_NAME: str
      SECRETS_MANAGER_DB_CREDENTIALS_KEY: str
      RDS_MYSQL_HOST: str # Handle the renaming with a factory for each enviroment in the settings class


class StagingFrontendOutputs(BaseModel):
      EC2_APP_SERVER_PRIVATE_IP: str
      

class StagingAnsibleOutputs(BaseModel):
      AWS_MAIN_REGION: str
      EC2_BASTION_SERVER_PUBLIC_IP: str
      EC2_APP_SERVER_PRIVATE_IP: str
      EC2_APP_SERVER_SSH_USER: str
      EC2_BASTION_SERVER_SSH_USER: str
      EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH: str