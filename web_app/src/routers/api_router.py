# Внешние зависимости
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.crud import (sql_get_info, sql_get_free_legislation, sql_update_text, sql_update_binary,
                              sql_get_legislation_by_not_binary_pdf, sql_get_ready_legislation,
                              sql_delete_ready_legislation)
from web_app.src.schemas import (InfoWorkerResponse, SchemeLegislation, SchemeTextLegislation,
                                 SchemeBinaryLegislation, RemoveWorkerRequest, SchemeNumberLegislation,
                                 SchemeDeleteLegislation)
from web_app.src.utils import redis_service
from web_app.src.dependencies import get_client_ip


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
    total_unloaded_count = await redis_service.get_total_unloaded_data()

    return {
        "Всего записей": stats["total"],
        "Записей с бинарными данными документов": stats["has_binary_pdf"],
        "Записей с текстом документов": stats["has_text"],
        "Записей выгруженных из бд": total_unloaded_count,
        "Процент бинарных данных": f"{(stats["has_binary_pdf"] + total_unloaded_count) / stats["total"] \
            if stats["total"] > 0 else 0}%",
        "Процент текстовых данных": f"{(stats["has_text"] + total_unloaded_count) / stats["total"] \
            if stats["total"] > 0 else 0}%",
        "Процент выгруженных данных": f"{total_unloaded_count / stats["total"] \
            if stats["total"] > 0 else 0}%"
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


@router.get(
    path="/legislation/free",
    response_model=List[SchemeBinaryLegislation],
    summary="Возвращаем данные законопроектов, которые можно обработать"
)
async def get_free_legislation(
    worker_id: int,
    limit: int = 10,
    client_ip: str = Depends(get_client_ip)
):
    reservation_legislation_ids = await redis_service.get_legislation_ids()

    legislation = await sql_get_free_legislation(
        reservation_legislation_ids=reservation_legislation_ids,
        limit=limit
    )

    await redis_service.ping_worker(
        ip=client_ip,
        worker_id=worker_id,
        processed_data=0,
        legislation_ids=[l.id for l in legislation]
    )

    return legislation


@router.get(
    path="/legislation/not_binary",
    response_model=List[SchemeNumberLegislation],
    summary="Возвращаем публикационные номера законопроектов, которые не имеют бинарных данных"
)
async def get_not_binary_legislation():
    legislation = await sql_get_legislation_by_not_binary_pdf
    return legislation


@router.get(
    path="/legislation/ready",
    response_model=List[SchemeLegislation],
    summary="Передаем данные о выгрузке"
)
async def get_ready_legislation(limit: int = 10):
    legislation = await sql_get_ready_legislation(limit=limit)
    return legislation


@router.patch(
    path="/legislation/update/binary",
    response_class=JSONResponse,
    summary="Обновляем бинарные данные pdf файла законопроекта"
)
async def update_binary_legislation(
        data: SchemeBinaryLegislation
):
    await sql_update_binary(
        legislation_id=data.id,
        content=data.binary
    )

    return {"status": "success"}


@router.patch(
    path="/legislation/update/text",
    response_class=JSONResponse,
    summary="Обновляем текст законопроекта"
)
async def update_text_legislation(
        data: SchemeTextLegislation,
        client_ip: str = Depends(get_client_ip)
):
    await sql_update_text(
        legislation_id=data.id,
        content=data.text
    )

    await redis_service.ping_worker(
        ip=client_ip,
        worker_id=data.worker_id,
        processed_data=1
    )

    return {"status": "success"}


@router.delete(
    path="/worker/delete",
    response_class=JSONResponse,
    summary="Удаляем обработчик"
)
async def delete_worker(
    data: RemoveWorkerRequest,
    client_ip: str = Depends(get_client_ip)
):
    message = await redis_service.delete_worker(
        ip=client_ip,
        worker_id=data.worker_id
    )
    return {"message": message}


@router.delete(
    path="/legislation/ready/delete",
    response_class=JSONResponse,
    summary="Удаляем выгруженные законопроекты"
)
async def update_text_legislation(data: SchemeDeleteLegislation):
    delete_count = await sql_delete_ready_legislation(legislation_ids=data.ids)

    await redis_service.add_unloaded_data(unloaded_count=delete_count)

    return {"status": "success", "delete_count": delete_count}
