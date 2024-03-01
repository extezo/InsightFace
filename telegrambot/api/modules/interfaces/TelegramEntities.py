import pydantic
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    current_send_button_id: int = Field(default=-1)
    selected: Optional[List[bool]] = Field(default=[])
    extract_embedding: Optional[bool] = Field(default=True,
                                                       example=True,
                                                       description='Extract face embeddings (otherwise only detect \
                                                       faces)')
