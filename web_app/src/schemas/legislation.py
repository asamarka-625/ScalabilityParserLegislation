# Внешние зависимости
from typing import Annotated, List
from datetime import datetime
import base64
from pydantic import BaseModel, Field, field_serializer, field_validator


# Схема данных законодательства
class SchemeReadyLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    binary_pdf: bytes
    text: Annotated[str, Field(strict=True, strip_whitespace=True)]

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
    binary: str

    @field_validator('binary', mode='before')
    @classmethod
    def validate_binary(cls, v):
        # Если приходит bytes, декодируем в base64 строку
        if isinstance(v, bytes):
            return base64.b64encode(v).decode('utf-8')
        # Если приходит str, возвращаем как есть (ожидаем base64 строку)
        return v


# Схема публикационного номера законопроекта
class SchemeNumberLegislation(BaseModel):
    id: Annotated[int, Field(ge=1)]
    publication_number: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема для удаления законопроектов
class SchemeDeleteLegislation(BaseModel):
    ids: List[Annotated[int, Field(ge=1)]]