import pydantic
from pydantic import BaseModel
from typing import List, Optional


class Images(BaseModel):
    data: List[str] = pydantic.Field(default=[], example=None, description='List of base64 encoded images')


class BodyExtract(BaseModel):
    images: Images
    extract_embedding: Optional[bool] = pydantic.Field(default=True,
                                                       example=True,
                                                       description='Extract face embeddings (otherwise only detect \
                                                       faces)')
