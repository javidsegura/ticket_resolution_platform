from pydantic import BaseModel


class DevBackendOutputs(BaseModel):
      # AWS
      S3_MAIN_BUCKET_NAME: str

      # AZURE
      AZURE_STORAGE_CONTAINER_NAME: str

class DevFrontendOutputs(BaseModel):
      ...

class DevAnsibleOutputs(BaseModel):
      ...
