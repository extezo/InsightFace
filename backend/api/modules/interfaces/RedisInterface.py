import pydantic
from typing import List, Dict
from pydantic import BaseModel


class Image(BaseModel):
    bboxes: List[List[int]] = pydantic.Field(default=[[]], example=None, description='List of image bounding boxes')
    vectors: List[List[float]] = pydantic.Field(default=[[]], example=None, description='List of faces\' vectors')


class User(BaseModel):
    images: Dict[str, Image] = pydantic.Field(default={}, example=None, description='Dictionary of user\'s images')