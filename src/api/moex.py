import asyncio
import pandas as pd #Для работы с таблицами данных (дата фреймы)
from numpy import nan
from datetime import date, timedelta

BASE_HOST = "http://iss.moex.com" #Задаем базовый адрес запроса для облигаций

def filter_bonds(data_bonds):
    columns = ["BOARDID", "SHORTNAME", "SECID", "LISTLEVEL", "NUMTRADES", "VALUE", "LOW", "HIGH", "CLOSE",
               "LEGALCLOSEPRICE", "ACCINT", "WAPRICE", "YIELDCLOSE", "OPEN", "VOLUME", "MARKETPRICE2", "MARKETPRICE",
               "MP2VALTRD", "MARKETPRICE3TRADESVALUE", "MATDATE", "DURATION", "YIELDATWAP", "COUPONPERCENT",
               "COUPONVALUE", "COUPONFREQUENCY", "DOHOD", "AKRA", "EXPERT", "OTHERCREDITSTATUS", "BUYBACKDATE",
               "LASTTRADEDATE", "FACEVALUE"]

    data_bonds = data_bonds.replace(r'^\s*$', nan, regex=True)

    filtred_bonds = data_bonds[
        (data_bonds['FACEUNIT'] == 'RUB') &
        (data_bonds['OFFERDATE'].isnull()) &
        (data_bonds['CALLOPTIONDATE'].isnull()) &
        (data_bonds['MATDATE'] > str(date.today() + timedelta(days=30)))
        ]

    filtred_bonds = filtred_bonds.sort_values(by="COUPONPERCENT", ascending=False)

    print("Filtered list: ", len(filtred_bonds))

    df_bonds = pd.DataFrame(filtred_bonds, columns=columns)
    df_bonds[['DOHOD', 'AKRA', 'EXPERT', 'OTHERCREDITSTATUS']] = df_bonds[
        ['DOHOD', 'AKRA', 'EXPERT', 'OTHERCREDITSTATUS']].astype('object')
    
    return df_bonds

async def get_bonds_page(apiClient, index=0):
    url = f"{BASE_HOST}/iss/history/engines/stock/markets/bonds/boards/TQCB/securities.json"
    url_opt = f"?start={index}"
    url_next_page = url + url_opt
    return await apiClient.get_json(url_next_page)


async def get_bonds(apiClient):
    total, step = (await get_bonds_page(apiClient))['history.cursor']['data'][0][1:]

    async def add_bond_page(index):
        result = await get_bonds_page(apiClient, index)
        resp_date = result['history']['data']
        col_name = result['history']['columns']
        return pd.DataFrame(resp_date, columns=col_name)

    data_bonds = await asyncio.gather(*[add_bond_page(i) for i in range(0, total, step)])
    return pd.concat(data_bonds, ignore_index=True)

async def get_securities_bond(apiClient, bond):
    url = f"{BASE_HOST}/iss/securities/{bond}.json"
    return await apiClient.get_json(url)

