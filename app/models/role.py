from enum import Enum
from typing import List

from pydantic import BaseModel

from app.core.config import (
    ROLE_LICENSE_PUBLISHER,
    ROLE_PROJECT_CREATOR,
    ROLE_PROJECT_MANAGER,
    ROLE_PROJECT_MEMBER,
    ROLE_SUPERUSER
)

# from app.core.config import ROLE_PROJECT_LEAD
# from app.core.config import ROLE_PROJECT_MEMBER
# from app.core.config import ROLE_CLASSROOM_HOST


class RoleEnum(Enum):
    superuser        = ROLE_SUPERUSER
    projectcreator   = ROLE_PROJECT_CREATOR
    projectmanager   = ROLE_PROJECT_MANAGER
    projectmember    = ROLE_PROJECT_MEMBER
    licensepublisher = ROLE_LICENSE_PUBLISHER


class Roles(BaseModel):
    roles: List[RoleEnum]
