from pydantic import BaseModel


class StagingConnectionModel(BaseModel):
    EC2_APP_SERVER_SSH_USER: str
    EC2_APP_SERVER_PRIVATE_IP: str
    EC2_BASTION_SERVER_PUBLIC_IP: str
    EC2_BASTION_SERVER_SSH_USER: str
    SSH_KEY_SECRET_NAME: str  # Fetched from AWS Secrets Manager
    RDS_MYSQL_HOST: str
