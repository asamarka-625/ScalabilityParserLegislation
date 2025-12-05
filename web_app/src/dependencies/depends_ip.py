# Внешние зависимости
from fastapi import Request


# Dependency для получения IP клиента
def get_client_ip(request: Request) -> str:
    # Проверяем все возможные заголовки
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Берем первый IP (оригинальный клиент)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return "no_ip"