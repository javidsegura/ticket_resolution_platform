from pydantic import BaseModel


class ProdConnectionModelAWS(BaseModel):
      EC2_APP_SERVER_SSH_USER : str
      EC2_APP_SERVER_PUBLIC_IP : str
      EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH: str
      RDS_MYSQL_HOST : str

class ProdConnectionModelAzure(BaseModel):
      VM_APP_SERVER_SSH_USER : str
      VM_APP_SERVER_PUBLIC_IP : str
      VM_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH: str
      MYSQL_HOST : str



class StagingConnectionModel(BaseModel):
      EC2_APP_SERVER_SSH_USER : str
      EC2_APP_SERVER_PRIVATE_IP : str
      EC2_BASTION_SERVER_PUBLIC_IP : str
      EC2_BASTION_SERVER_SSH_USER : str
      EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH: str
      RDS_MYSQL_HOST : str
