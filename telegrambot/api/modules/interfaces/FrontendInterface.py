import pydantic
from typing import Optional, List, Dict
from pydantic import BaseModel


class UploadImages(BaseModel):
    data: List[str] = pydantic.Field(default=None, example=None, description='List of base64 encoded images')


class SelectFace(BaseModel):
    id: Dict[str, int] = pydantic.Field(default={}, example=None, description='Dictionary of image IDs with selected face')
