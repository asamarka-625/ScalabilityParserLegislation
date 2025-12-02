# Внешние зависимости
from typing import List
from fastapi import APIRouter
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.crud import sql_get_info, sql_get_legislation_ids
from web_app.src.schemas import InfoWorkerResponse, PingWorkerRequest, RemoveWorkerRequest, LegislationWorkerRequest
from web_app.src.utils import redis_service


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)


@router.get(
    path="/db/stats",
    response_class=JSONResponse,
    summary="Информация по заполнению базы данных"
)
async def get_info_from_db():
    stats = await sql_get_info()

    return {
        "Всего записей": stats["total"],
        "Записей с бинарными данными документов": stats["has_binary_pdf"],
        "Записей с текстом документов": stats["has_text"],
        "Записей выгруженных из бд": stats["loaded"],
        "Процент бинарных данных": f"{(stats["has_binary_pdf"] + stats["loaded"]) / stats["total"] \
            if stats["total"] > 0 else 0}%",
        "Процент текстовых данных": f"{(stats["has_text"] + stats["loaded"]) / stats["total"] \
            if stats["total"] > 0 else 0}%",
        "Процент выгруженных данных": f"{stats["loaded"] / stats["total"]}%"
    }


@router.get(
    path="/redis/stats",
    response_class=JSONResponse,
    summary="Информация по Redis"
)
async def get_info_from_redis():
    stats = await redis_service.get_stats()
    return stats


@router.get(
    path="/worker/stats",
    response_model=List[InfoWorkerResponse],
    summary="Информация по активным обработчикам"
)
async def get_info_from_workers():
    result = await redis_service.get_workers()
    return result


@router.post(
    path="/legislation/ids",
    response_class=JSONResponse,
    summary="Возвращаем ids законопроектов, которые можно обработать"
)
async def get_legislation_ids(data: LegislationWorkerRequest):
    reservation_legislation_ids = await redis_service.get_legislation_ids()

    if reservation_legislation_ids:
        legislation_ids = await sql_get_legislation_ids(
            reservation_legislation_ids=reservation_legislation_ids,
            limit=data.limit
        )

    else:
        legislation_ids = []

    await redis_service.ping_worker(
        ip=data.ip,
        processed_data=0,
        legislation_ids=legislation_ids
    )

    return {"legislation_ids": legislation_ids}


@router.post(
    path="/worker/ping",
    response_class=JSONResponse,
    summary="Пингуем обработчик"
)
async def ping_worker(data: PingWorkerRequest):
    await redis_service.ping_worker(**data.model_dump())
    return {"status": "success"}


@router.post(
    path="/worker/delete",
    response_class=JSONResponse,
    summary="Удаляем обработчик"
)
async def delete_worker(data: RemoveWorkerRequest):
    message = await redis_service.delete_worker(ip=data.ip)
    return {"message": message}