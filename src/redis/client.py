import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import redis.asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


class RedisClient:
    def __init__(self, redis_url: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        expire_at: Optional[datetime] = None,
    ) -> None:
        """Сохраняет значение. Значение автоматически сериализуется в JSON."""
        kwargs = {}
        if expire_at is not None:
            kwargs["exat"] = expire_at
        elif ttl_seconds is not None:
            kwargs["ex"] = ttl_seconds

        await self.redis.set(key, json.dumps(value, ensure_ascii=False), **kwargs)

    async def get(self, key: str) -> Optional[Any]:
        """Читает значение по ключу. Возвращает None, если ключа нет или TTL истёк."""
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, key: str) -> bool:
        return await self.redis.delete(key) > 0

    async def close(self):
        await self.redis.aclose()


async def main():
    client = RedisClient()

    try:
        # Запись с TTL в секундах
        await client.set("user:1", {"name": "Alice", "role": "admin"}, ttl_seconds=5)

        # Запись с точной датой истечения
        await client.set(
            "user:2",
            {"name": "Bob", "role": "user"},
            expire_at=datetime.now() + timedelta(seconds=10),
        )

        # Чтение
        print(await client.get("user:1"))
        print(await client.get("user:2"))

        # Ждём, пока первая запись истечёт
        await asyncio.sleep(6)
        print("После ожидания:")
        print(await client.get("user:1"))  # None
        print(await client.get("user:2"))  # ещё жива

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())