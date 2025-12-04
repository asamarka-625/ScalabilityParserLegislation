# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема получения информации об обработчике
class InfoWorkerResponse(BaseModel):
    ip: Annotated[str, Field(strict=True, strip_whitespace=True)]
    worker_id: Annotated[int, Field(ge=0)]
    first_connection_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    last_connection_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    active_time: Annotated[str, Field(strict=True, strip_whitespace=True)]
    total_processed_data: Annotated[int, Field(ge=0)]


# Схема запроса удаления обработчика
class RemoveWorkerRequest(BaseModel):
    worker_id: Annotated[int, Field(ge=0)]