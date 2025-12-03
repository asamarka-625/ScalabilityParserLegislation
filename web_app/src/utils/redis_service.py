# Внешние зависимости
from typing import Optional, List
from datetime import datetime
import json
import redis.asyncio as redis
# Внутренние модули
from web_app.src.core import config
from web_app.src.schemas import InfoWorkerResponse
from web_app.src.crud import sql_valid_legislation_ids_from_worker


class RedisService:
    def __init__(self):
        self.redis_url = config.REDIS_URL
        self.redis: Optional[redis.Redis] = None
        self.worker_prefix = "worker:"
        self.legislation_ids_key = "legislation_ids"
        self.total_unloaded_data_key = "total_unloaded_data"

    async def init_redis(self):
        """Инициализация подключения к Redis"""
        config.logger.info("Инициализируем соединение Redis")

        if not self.redis:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def close_redis(self):
        """Закрытие подключения к Redis"""
        config.logger.info("Закрываем соединение Redis")

        if self.redis:
            await self.redis.close()

    async def add_unloaded_data(self, unloaded_count: int):
        """Увеличиваем счетчик выгруженных данных"""
        await self.redis.incrby(self.total_unloaded_data_key, unloaded_count)

    async def get_total_unloaded_data(self):
        """Получаем количество выгруженных данных"""
        total_unloaded_count = await self.redis.get(self.total_unloaded_data_key)
        return int(total_unloaded_count) if total_unloaded_count is not None else 0

    async def ping_worker(
        self,
        ip: str,
        worker_id: int,
        processed_data: int,
        expire_seconds: int = 180,
        legislation_ids: Optional[List[int]] = None
    ):
        """Сохранение/обновление обработчика в Redis"""
        if legislation_ids is not None:
            existing_ids_json = await self.redis.get(self.legislation_ids_key)

            if existing_ids_json:
                existing_ids = json.loads(existing_ids_json)
                combined_ids = list(dict.fromkeys(existing_ids + legislation_ids))

            else:
                combined_ids = legislation_ids

            # Сериализуем список в JSON для хранения в Redis
            combined_ids_json = json.dumps(combined_ids)

            await self.redis.set(
                self.legislation_ids_key,
                combined_ids_json
            )

        key = f"{self.worker_prefix}{ip}:{worker_id}"
        current_time = datetime.now().isoformat()

        if await self.redis.exists(key):
            async with self.redis.pipeline() as pipeline:
                await pipeline.hincrby(key, 'total_processed_data', processed_data)
                await pipeline.hset(key, 'last_connection_time', current_time)

                if legislation_ids is not None:
                    legislation_ids_json = json.dumps(legislation_ids)
                    await pipeline.hset(key, 'legislation_ids', legislation_ids_json)

                await pipeline.expire(key, expire_seconds)
                await pipeline.execute()

        else:
            worker_data = {
                'ip': ip,
                'worker_id': worker_id,
                'first_connection_time': current_time,
                'last_connection_time': current_time,
                'total_processed_data': processed_data
            }

            if legislation_ids is not None:
                legislation_ids_json = json.dumps(legislation_ids)
                worker_data['legislation_ids'] = legislation_ids_json

            async with self.redis.pipeline() as pipeline:
                await pipeline.hset(key, mapping=worker_data)
                await pipeline.expire(key, expire_seconds)
                await pipeline.execute()

    async def delete_worker(self, ip: str, worker_id: int) -> str:
        """Удаление обработчика по IP с обновлением списка legislation_ids"""
        key = f"{self.worker_prefix}{ip}:{worker_id}"

        # 1. Получаем данные воркера и вычисляем valid_legislation_ids
        if not await self.redis.exists(key):
            return f"Worker {ip} not found for deletion"

        worker_data = await self.redis.hgetall(key)
        legislation_ids_json = worker_data.get('legislation_ids')

        valid_legislation_ids = []
        if legislation_ids_json:
            try:
                worker_legislation_ids = json.loads(legislation_ids_json)
                valid_legislation_ids = await sql_valid_legislation_ids_from_worker(
                    worker_legislation_ids=worker_legislation_ids
                )
            except json.JSONDecodeError as e:
                config.logger.error(f"Error parsing legislation_ids for worker {ip}: {e}")

        # 2. Атомарно обновляем список и удаляем воркера
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                # Начинаем наблюдение за ключами
                await pipe.watch(key, self.legislation_ids_key)

                # Проверяем, что воркер все еще существует
                if not await self.redis.exists(key):
                    return f"Worker {ip} not found for deletion"

                # Начинаем транзакцию
                pipe.multi()

                # Обновляем общий список
                if valid_legislation_ids:
                    existing_ids_json = await self.redis.get(self.legislation_ids_key)

                    if existing_ids_json:
                        existing_ids = json.loads(existing_ids_json)
                        updated_ids = [
                            id_ for id_ in existing_ids
                            if id_ not in valid_legislation_ids
                        ]
                        updated_ids_json = json.dumps(updated_ids)
                        await pipe.set(self.legislation_ids_key, updated_ids_json)

                # Удаляем воркера
                await pipe.delete(key)

                # Выполняем транзакцию
                await pipe.execute()

            except redis.WatchError:
                # Если другой процесс изменил данные, повторяем всю операцию
                config.logger.warning(f"Concurrency conflict for worker {ip}, retrying...")
                return await self.delete_worker(ip=ip, worker_id=worker_id)

            finally:
                await pipe.reset()

        message = f"Worker {ip} deleted successfully"
        if valid_legislation_ids:
            config.logger.info(
                f"Updated legislation_ids after removing worker {ip}. "
                f"Removed {len(valid_legislation_ids)} valid IDs"
            )

        config.logger.info(message)
        return message

    async def get_legislation_ids(self) -> List[int]:
        """Получение списка законодательных актов для обработки из Redis legislation_ids"""
        try:
            legislation_ids_json = await self.redis.get(self.legislation_ids_key)

            if legislation_ids_json:
                legislation_ids = json.loads(legislation_ids_json)
                return legislation_ids

            else:
                return []

        except json.JSONDecodeError as e:
            config.logger.error(f"Error decoding legislation_ids from Redis: {e}")
            return []

        except Exception as e:
            config.logger.error(f"Error getting legislation_ids from Redis: {e}")
            return []

    async def get_workers(self) -> List[InfoWorkerResponse]:
        """Получаем информацию по обработчикам"""
        worker_keys = await self.redis.keys(f"{self.worker_prefix}*")

        workers_info = []

        for key in worker_keys:
            worker_data = await self.redis.hgetall(key)

            first_connection_time = datetime.fromisoformat(worker_data['first_connection_time'])
            last_connection_time = datetime.fromisoformat(worker_data['last_connection_time'])

            info = InfoWorkerResponse(
                ip=worker_data["ip"],
                worker_id=int(worker_data["worker_id"]),
                first_connection_time=first_connection_time.strftime("%d %B %Y %H:%M:%S"),
                last_connection_time=last_connection_time.strftime("%d %B %Y %H:%M:%S"),
                active_time=(datetime.min + (last_connection_time - first_connection_time)).strftime("%H:%M:%S"),
                total_processed_data=worker_data["total_processed_data"]
            )

            workers_info.append(info)

        return workers_info

    async def get_stats(self) -> dict:
        """Статистика обработчиков"""
        worker_keys = await self.redis.keys(f"{self.worker_prefix}*")

        workers_info = []
        total_processed = 0

        for key in worker_keys:
            worker_data = await self.redis.hgetall(key)
            dt_first_connection_time = datetime.fromisoformat(worker_data["first_connection_time"])
            dt_last_connection_time = datetime.fromisoformat(worker_data["last_connection_time"])
            worker_data["first_connection_time"] = dt_first_connection_time.strftime("%d %B %Y %H:%M:%S")
            worker_data["last_connection_time"] = dt_last_connection_time.strftime("%d %B %Y %H:%M:%S")

            workers_info.append(worker_data)
            total_processed += int(worker_data.get('total_processed_data', 0))

        return {
            "total_workers": len(worker_keys),
            "total_processed_data": total_processed,
            "workers": workers_info,
            "memory_usage": await self.redis.info('memory')
        }


_instance = None


def get_redis_service() -> RedisService:
    global _instance
    if _instance is None:
        _instance = RedisService()

    return _instance