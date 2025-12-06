from pydantic import BaseModel


class ProdConnectionModelAWS(BaseModel):
    EC2_APP_SERVER_SSH_USER: str
    EC2_APP_SERVER_PUBLIC_IP: str
    SSH_KEY_SECRET_NAME: str  # Fetched from AWS Secrets Manager
    RDS_MYSQL_HOST: str


class ProdConnectionModelAzure(BaseModel):
    VM_APP_SERVER_SSH_USER: str
    VM_APP_SERVER_PUBLIC_IP: str
    VM_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH: str  # Azure still uses local file
    MYSQL_HOST: str
