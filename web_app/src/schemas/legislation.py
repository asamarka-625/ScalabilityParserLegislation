# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема запроса выгрузки
class UnloadDataRequest(BaseModel):
    count: Annotated[int, Field(ge=0)]