import pydantic
from typing import Optional, List, Dict

from PIL import Image
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    current_send_button_id: List[int] = Field(default=[])
    selected: Optional[List[bool]] = Field(default=[])
    sent_images_ids: List[int] = Field(default=[])
    selected_num: int = Field(default=0)
    is_compare_phase: Optional[bool] = Field(default=False)
    current_error_send_id: int = Field(default=-1)
    current_error_too_many_selected: int = Field(default=-1)
    base64images: List[str] = Field(default=[])
    current_images: list = Field(default=[])
    current_faces: List[int] = Field(default=[])
    images_ids: List[str] = Field(default=[])  # refactor later
    images_id_dict: dict = Field(default={},
                                 description='dict id:img only for draw bboxes, ')  # refactor later
