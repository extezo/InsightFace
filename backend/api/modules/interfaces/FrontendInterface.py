import pydantic
from typing import Optional, List
from pydantic import BaseModel


class UploadImages(BaseModel):
    name: List[str] = pydantic.Field(default=None, example=None, description='List of base64 encoded images')


class SelectFace(BaseModel):
    faces: List[int] = pydantic.Field(default=None, example=None, description='List of face IDs (one per image, the '
                                                                              'same order as displayed)')
