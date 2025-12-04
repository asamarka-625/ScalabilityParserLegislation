# Внешние зависимости
from typing import Annotated, List
from datetime import datetime
from pydantic import BaseModel, Field


# Схема данных законодательства
class SchemeLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    publication_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    publication_date: datetime
    link_pdf: Annotated[str, Field(strict=True, strip_whitespace=True)]
    binary_pdf: bytes
    text: Annotated[str, Field(strict=True, strip_whitespace=True)]
    law_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    authority_id: Annotated[int, Field(ge=1)]


# Схема текста законодательства
class SchemeTextLegislation(BaseModel):
    worker_id: Annotated[int, Field(ge=0)]
    id: Annotated[int, Field(ge=1)]
    text: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема бинарных данных pdf файла законодательства
class SchemeBinaryLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    binary: bytes


# Схема публикационного номера законопроекта
class SchemeNumberLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    publication_number: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема для удаления законопроектов
class SchemeDeleteLegislation(BaseModel):
    ids: List[Annotated[int, Field(ge=1)]]