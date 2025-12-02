# Внешние зависимости
from fastapi import Request


# Dependency для получения IP клиента
def get_client_ip(request: Request) -> str:
    return request.client.host or "no_ip"