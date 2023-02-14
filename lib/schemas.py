from typing import Optional

from pydantic import BaseModel
from deluge.utils import MetaData


class QuestMagnet(BaseModel):
    name: str
    display_name: str
    magnet: str
    version: float
    filesize: int
    date_added: float
    id: str
    metadata: Optional[MetaData]

    @property
    def uri(self) -> str:
        return self.magnet
