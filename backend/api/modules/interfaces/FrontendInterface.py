import pydantic
from typing import List, Dict
from pydantic import BaseModel


class UploadImages(BaseModel):
    data: List[str] = pydantic.Field(default=None, example=None, description='List of base64 encoded images')


class SelectFaces(BaseModel):
    id: Dict[str, List[int]] = pydantic.Field(default={}, example=None, description='Dictionary of image IDs with selected face')


class SelectFace(BaseModel):
    id: Dict[str, List[int]] = pydantic.Field(default={}, example=None,
                                              description='Dictionary of image IDs with selected face')

