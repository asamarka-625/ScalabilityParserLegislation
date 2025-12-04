# Внешние зависимости
from typing import Annotated, List
from datetime import datetime
import base64
from pydantic import BaseModel, Field, field_serializer


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

    @field_serializer('binary_pdf')
    def serialize_binary_pdf(self, binary_pdf: bytes, _info):
        if binary_pdf:
            return base64.b64encode(binary_pdf).decode('utf-8')
        raise ValueError("Not binary data")


# Схема текста законодательства
class SchemeTextLegislation(BaseModel):
    worker_id: Annotated[int, Field(ge=0)]
    id: Annotated[int, Field(ge=1)]
    text: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема бинарных данных pdf файла законодательства
class SchemeBinaryLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    binary: bytes

    @field_serializer('binary')
    def serialize_binary(self, binary: bytes, _info):
        if binary:
            return base64.b64encode(binary).decode('utf-8')
        raise ValueError("Not binary data")


# Схема публикационного номера законопроекта
class SchemeNumberLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    publication_number: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема для удаления законопроектов
class SchemeDeleteLegislation(BaseModel):
    ids: List[Annotated[int, Field(ge=1)]]