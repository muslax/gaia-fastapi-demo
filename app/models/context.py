from pydantic import BaseModel


class ProjectContext(BaseModel):
    prj_id: str = None
    channel: str = None
    # username: str = None
    # user_id: str = None