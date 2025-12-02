# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема получения информации об обработчике
class InfoWorkerResponse(BaseModel):
    ip: Annotated[str, Field(strict=True, strip_whitespace=True)]
    first_connection_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    last_connection_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    active_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    total_processed_data: Annotated[int, Field(ge=0)]


# Схема запроса для получения ids законопроектов
class LegislationWorkerRequest(BaseModel):
    ip: Annotated[str, Field(strict=True, strip_whitespace=True)]
    limit: Annotated[int, Field(ge=1)]


# Схема запроса пинга обработчика
class PingWorkerRequest(BaseModel):
    ip: Annotated[str, Field(strict=True, strip_whitespace=True)]
    processed_data: Annotated[int, Field(ge=0)]
    expire_seconds: Annotated[int, Field(ge=1)]


# Схема запроса удаления обработчика
class RemoveWorkerRequest(BaseModel):
    ip: Annotated[str, Field(strict=True, strip_whitespace=True)]