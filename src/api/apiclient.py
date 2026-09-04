import aiohttp
from retrying import retry

from src.config import config
from src.redis import client

client_config = config['params']['client']

class APIClient:
    def __init__(self):
        # Сессия создается один раз
        self.session = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=client_config['limit'],  # Максимум 100 открытых соединений ВЕЗДЕ
            limit_per_host=client_config['limit_per_host'],  # Максимум 10 одновременных соединений НА ОДИН ХОСТ
            ttl_dns_cache=300,  # Кэшировать DNS на 5 минут (ускоряет работу)
            enable_cleanup_closed=True  # Очищать закрытые SSL соединения
        )
        # Сессия создается только здесь, внутри async контекста
        self.session = aiohttp.ClientSession(connector=connector)
        # self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Сессия автоматически закроется при выходе из блока async with
        if self.session and not self.session.closed:
            await self.session.close()

    @retry(wait_exponential_multiplier=100, wait_exponential_max=10000)
    async def get_json(self, url):
        async with self.session.get(url) as resp:
            return await resp.json()

    @retry(wait_exponential_multiplier=100, wait_exponential_max=10000)
    async def get_text(self, url):
        async with self.session.get(url) as resp:
            return await resp.text()
