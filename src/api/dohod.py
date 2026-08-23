BASE_HOST = "https://analytics.dohod.ru"

async def get_dohod_bond(apiClient, bond):
    url = f"{BASE_HOST}/bond/{bond['SECID']}"
    html = await apiClient.get_text(url)
    return html