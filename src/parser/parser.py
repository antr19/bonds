import asyncio
from datetime import datetime, date, timedelta

from src.api.apiclient import APIClient
from src.api.moex import get_bonds, filter_bonds
from src.api.dohod import get_dohod_bond
from src.parser.html_parser import parse
from src.redis.client import RedisClient

async def get_dohod_data(apiClient, redisClient, index, bond):
    if not await redisClient.get(f"client_status:{bond['SECID']}"):
        print(
            f"[{datetime.now().timestamp()}] Request {bond['SHORTNAME']} - {bond['SECID']} from https://analytics.dohod.ru")
        html = await get_dohod_bond(apiClient, bond)
        print(
            f"[{datetime.now().timestamp()}] Response {bond['SHORTNAME']} - {bond['SECID']} from https://analytics.dohod.ru")

        credit_statues = parse(html)
        await redisClient.set(f"client_status:{bond['SECID']}", credit_statues, expire_at=datetime.now() + timedelta(days=21))

async def parser():
    async with APIClient() as apiClient:
        data_bonds = await get_bonds(apiClient)
        print("Full list: ",len(data_bonds))

        filtered_bonds = filter_bonds(data_bonds)

        redisClient = RedisClient()
        tasks = [get_dohod_data(apiClient, redisClient, index, bond) for index, bond in filtered_bonds.iterrows()]

        await asyncio.gather(*tasks)
        await redisClient.close()

    print("Parser:", "finished")

