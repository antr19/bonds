import asyncio
import datetime
import json
from datetime import date, datetime

from src.api.apiclient import APIClient
from src.api.moex import get_bonds, filter_bonds, get_securities_bond, get_emitter_page
from src.redis.client import RedisClient
from src.tinkoff.client import TBankPortfolioREST
from src.config import config

from src.telegram.client import send_data_to_telegram

report_config = config['params']['report']

async def extend_bond(apiClient, redisClient, index, bond, bonds):
    print(
        f"[{datetime.now().timestamp()}] Request {bond['SHORTNAME']} - {bond['SECID']} from https://iss.moex.com")
    result = await get_securities_bond(apiClient, bond['SECID'])

    for line in result['description']['data']:
        if line[0] == "LISTLEVEL":
            bonds.loc[index, 'LISTLEVEL'] = int(line[2])
        elif line[0] == "COUPONFREQUENCY":
            bonds.loc[index, 'COUPONFREQUENCY'] = int(line[2])
        elif line[0] == "EMITTER_ID":
            bonds.loc[index, 'INN'] = (await get_emitter_page(apiClient, int(line[2])))['emitter']['data'][0][3]

    credit_status = await redisClient.get(f"client_status:{bond['SECID']}")

    bonds.loc[index, 'DOHOD'] = credit_status.get('dohod', None)
    bonds.loc[index, 'AKRA'] = credit_status.get('akra', None)
    bonds.loc[index, 'EXPERT'] = credit_status.get('expert', None)
    bonds.loc[index, 'OTHERCREDITSTATUS'] = credit_status.get('other', None)

async def collector():
    message = "Еженедельный отчёт по облигациям!\n"
    paths = []

    report = {}
    async with APIClient() as apiClient:
        data_bonds = await get_bonds(apiClient)
        print("Full list: ",len(data_bonds))

        filtered_bonds = filter_bonds(data_bonds)

        redisClient = RedisClient()
        tasks = [extend_bond(apiClient, redisClient, index, bond, filtered_bonds) for index, bond in filtered_bonds.iterrows()]
        await asyncio.gather(*tasks)
        await redisClient.close()

        filtered_bonds.to_csv("full_result.csv", sep=';')
        try:
            filtered_bonds.to_excel("full_result.xlsx", index=False)
            paths.append("full_result.xlsx")
        except Exception as e:
            print("Error:", e)

        filtered_short_bonds = filtered_bonds[
            (filtered_bonds['LISTLEVEL'] < 3) &
            (filtered_bonds['COUPONFREQUENCY'] > 3) &
            (filtered_bonds['MATDATE'] < str(date.today().replace(year=date.today().year + 1))) &
            (filtered_bonds['YIELDATWAP'] > report_config['yield_persent_short'])
            ]

        print("Short list:", len(filtered_short_bonds))
        report["maybe_income_assets"] = filtered_short_bonds.to_dict(orient='records')

        premium_filtered_short_bonds = filtered_bonds[
            (filtered_bonds['LISTLEVEL'] == 1) &
            (filtered_bonds['COUPONFREQUENCY'] > 3) &
            (filtered_bonds['YIELDATWAP'] > report_config['yield_persent_premiun'])
            ]

        print("Premium short list:", len(premium_filtered_short_bonds))
        report["maybe_safe_assets"] = premium_filtered_short_bonds.to_dict(orient='records')

        # filtered_short_bonds = short_data_bonds[(short_data_bonds['LISTLEVEL'] == '2') | (short_data_bonds['LISTLEVEL'] == '1')]

        filtered_short_bonds.to_csv("short_result.csv", sep=';')
        try:
            filtered_short_bonds.to_excel("short_result.xlsx", index=False)
            paths.append("short_result.xlsx")
        except Exception as e:
            print("Error:", "Short Result:", e)

        premium_filtered_short_bonds.to_csv("premium_result.csv", sep=';')
        try:
            premium_filtered_short_bonds.to_excel("premium_result.xlsx", index=False)
            paths.append("premium_result.xlsx")
        except Exception as e:
            print("Error:", "Premium Result:", e)


        t_client = TBankPortfolioREST()
        report["current_portfolio"] = await t_client.get_portfolio_for_ai(allowed_types=["bond"])
        with open("report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            paths.append("report.json")

        await send_data_to_telegram(message, paths)

        print("Collector:", "finished!")
