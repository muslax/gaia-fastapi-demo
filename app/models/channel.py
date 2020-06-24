from enum import Enum
from typing import List

from pydantic import BaseModel

from app.core.config import CHANNEL_GAIA
from app.core.config import CHANNEL_LICENSED
from app.core.config import CHANNEL_PERSONA
from app.core.config import CHANNEL_CLIENT
from app.core.config import CHANNEL_EXPERT


class ChannelEnum(Enum):
    gaia     = CHANNEL_GAIA
    licensed = CHANNEL_LICENSED
    persona  = CHANNEL_PERSONA
    client   = CHANNEL_CLIENT
    expert   = CHANNEL_EXPERT


class Channels(BaseModel):
    channels: List[ChannelEnum]
