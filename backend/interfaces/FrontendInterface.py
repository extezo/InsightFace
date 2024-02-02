import pydantic
from typing import Optional, List
from pydantic import BaseModel


class BodyUploadImages(BaseModel):
    name: List[str] = pydantic.Field(default=None, example=None, description='List of base64 encoded images')


class BodySelectFace(BaseModel):
    faces: List[int] = pydantic.Field(default=None, example=None, description='List of face IDs (one per image, the '
                                                                             'same order as displayed)')


class BodyUploadImagesResponse(BaseModel):
    data: List[List[int]] = pydantic.Field(default=None, example=None,
                                                 description='List of face IDs (one per image, the '
                                                             'same order as displayed)')
