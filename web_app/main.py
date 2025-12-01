# Внешние зависимости
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Внутренние модули
from web_app.src.core import config, setup_database
from web_app.src.routers import router
from web_app.src.utils import redis_service


async def startup():
    config.logger.info("Запускаем приложение...")
    await setup_database()
    await redis_service.init_redis()


async def shutdown():
    config.logger.info("Останавливаем приложение...")
    await redis_service.close_redis()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup логика
    await startup()
    yield
    # Shutdown логика
    await shutdown()


app = FastAPI(lifespan=lifespan)

# Подключение маршрутов
app.include_router(router)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', port=8000, reload=False)