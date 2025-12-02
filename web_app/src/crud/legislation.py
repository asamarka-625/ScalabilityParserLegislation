# Внешние зависимости
from typing import Dict, List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import DataLegislation
from web_app.src.core import connection


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


# Выдаем свободные ids законопроектов для обработки
@connection
async def sql_get_legislation_ids(
        reservation_legislation_ids: List[int],
        limit: int,
        session: AsyncSession
) -> List[int]:
    try:
        legislation_ids_result = await session.execute(
            sa.select(DataLegislation.id)
            .where(
                DataLegislation.id.notin_(reservation_legislation_ids),
                DataLegislation.binary_pdf != None,
                DataLegislation.text == None
            )
            .limit(limit)
        )
        legislation_ids = legislation_ids_result.scalars().all()

        return legislation_ids

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading legislation ids: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading legislation ids: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Находим не валидные
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