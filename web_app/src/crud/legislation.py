# Внешние зависимости
from typing import Dict, List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config, connection
from web_app.src.models import DataLegislation
from web_app.src.schemas import SchemeBinaryLegislation, SchemeNumberLegislation, SchemeLegislation



# Выводим статистику по данным
@connection
async def sql_get_info(session: AsyncSession) -> Dict[str, int]:
    try:
        stats_result = await session.execute(
            sa.select(
                sa.func.count().label('total'),
                sa.func.count(DataLegislation.binary_pdf).label('has_binary_pdf'),
                sa.func.count(DataLegislation.text).label('has_text')
            )
        )
        stats = stats_result.first()

        return {
            "total": stats.total,
            "has_binary_pdf": stats.has_binary_pdf,
            "has_text": stats.has_text
        }

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выдаем свободные данные законопроектов для обработки
@connection
async def sql_get_free_legislation(
        reservation_legislation_ids: List[int],
        limit: int,
        session: AsyncSession
) -> List[SchemeBinaryLegislation]:
    try:
        legislation_result = await session.execute(
            sa.select(DataLegislation.id, DataLegislation.binary_pdf)
            .where(
                DataLegislation.id.notin_(reservation_legislation_ids),
                DataLegislation.binary_pdf != None,
                DataLegislation.text == None
            )
            .limit(limit)
        )
        legislation = legislation_result.all()

        return [
            SchemeBinaryLegislation(
                id=legislation_id,
                binary=legislation_binary
            )
            for (legislation_id, legislation_binary) in legislation
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading free legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading free legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Находим валидные
@connection
async def sql_valid_legislation_ids_from_worker(
    worker_legislation_ids: List[int],
    session: AsyncSession
) -> List[int]:
    try:
        legislation_ids_result = await session.execute(
            sa.select(DataLegislation.id)
            .where(
                DataLegislation.id.in_(worker_legislation_ids),
                DataLegislation.binary_pdf != None,
                DataLegislation.text == None
           )
        )
        legislation_ids = legislation_ids_result.scalars().all()

        return legislation_ids

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading valid legislation ids: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading valid legislation ids: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Записываем текст PDf файла
@connection
async def sql_update_text(
    legislation_id: int,
    content: str,
    session: AsyncSession
) -> None:
    try:
        legislation_results = await session.execute(
            sa.select(DataLegislation)
            .where(DataLegislation.id == legislation_id)
        )

        legislation = legislation_results.scalar_one()
        legislation.text = content
        await session.commit()

    except NoResultFound:
        config.logger.error(f"Legislation not found by legislation id: {legislation_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legislation not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error update text: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error update text: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим все законы, у которых нет байт-кода PDF файла
@connection
async def sql_get_legislation_by_not_binary_pdf(
        session: AsyncSession
) -> List[SchemeNumberLegislation]:
    try:
        legislation_results = await session.execute(
            sa.select(DataLegislation.id, DataLegislation.publication_number)
            .where(DataLegislation.binary_pdf == None)
        )

        legislation = legislation_results.all()
        return [
            SchemeNumberLegislation(
                id=legislation_id,
                publication_number=legislation_publication_number
            )
            for (legislation_id, legislation_publication_number) in legislation
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error read legislation with none binary_pdf: {e}")

    except Exception as e:
        config.logger.error(f"Unexpected error read legislation with none binary_pdf: {e}")


# Записываем бинарный код PDF файла
@connection
async def sql_update_binary(
        legislation_id: int,
        content: bytes,
        session: AsyncSession
) -> None:
    try:
        legislation_results = await session.execute(
            sa.select(DataLegislation)
            .where(DataLegislation.id == legislation_id)
        )

        legislation = legislation_results.scalar_one()
        legislation.binary_pdf = content
        await session.commit()

    except NoResultFound:
        config.logger.error(f"Legislation not found by legislation_id: {legislation_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legislation not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error update binary_pdf: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error update binary_pdf: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выдаем готовые к выгрузке данные законопроектов для обработки
@connection
async def sql_get_ready_legislation(limit: int, session: AsyncSession) -> List[SchemeLegislation]:
    try:
        legislation_result = await session.execute(
            sa.select(DataLegislation)
            .where(
                DataLegislation.binary_pdf != None,
                DataLegislation.text != None
            )
            .limit(limit)
        )
        legislation = legislation_result.all()

        return [
            SchemeLegislation(**l.to_dict())
            for l in legislation
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading ready legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading ready legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Удаляем данные, которые уже выгрузили в таблицу
@connection
async def sql_delete_ready_legislation(
    legislation_ids: List[int],
    session: AsyncSession
) -> int:
    try:
        result = await session.execute(
            sa.delete(DataLegislation)
            .where(
                DataLegislation.id.in_(legislation_ids),
                DataLegislation.binary_pdf != None,
                DataLegislation.text != None
            )
        )
        await session.commit()

        return result.rowcount

    except SQLAlchemyError as e:
        config.logger.error(f"Database error delete ready legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error delete ready legislation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")