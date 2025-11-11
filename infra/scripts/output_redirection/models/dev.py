from pydantic import BaseModel


class DevBackendOutputs(BaseModel):
      S3_MAIN_BUCKET_NAME: str

class DevFrontendOutputs(BaseModel):
      ...

class DevAnsibleOutputs(BaseModel):
      ...