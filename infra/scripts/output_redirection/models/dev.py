from pydantic import BaseModel


class DevBackendOutputs(BaseModel):
      S3_MAIN_BUCKET_NAME: str
      AZURE_STORAGE_CONTAINER_NAME: str

class DevFrontendOutputs(BaseModel):
      ...

class DevAnsibleOutputs(BaseModel):
      ...