import pydantic
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    current_send_button_id: int = Field(default=-1)
    selected: Optional[List[bool]] = Field(default=[])
    is_compare_phase: Optional[bool] = Field(default=False)
    current_error_send_id: int = Field(default=-1)
    base64images:List[str] = Field(default=[])
    current_images: list = Field(default=[])
    images_ids:List[str]=Field(default=[]) #refactor later
    images_id_dict:dict = Field(default={},
                                description='dict id:img only for draw bboxes, ') #refactor later

    extract_embedding: Optional[bool] = Field(default=True,
                                                       example=True,
                                                       description='Extract face embeddings (otherwise only detect \
                                                       faces)')
