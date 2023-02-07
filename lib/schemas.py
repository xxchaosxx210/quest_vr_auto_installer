from typing import Optional

from pydantic import BaseModel
from deluge.utils import MetaData


class QuestMagnet(BaseModel):
    name: str
    magnet: str
    version: float
    filesize: int
    metadata: Optional[MetaData]

    @property
    def uri(self) -> str:
        return self.magnet
