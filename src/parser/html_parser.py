from bs4 import BeautifulSoup
import re

def get_status(text):
    check = re.findall('[ABC]+[+-]*', text)
    if check:
        return check[0]
    return None

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    res = {}

    # Поиск всех элементов с классом 'dohod-tag-name'
    elements = soup.find_all('div', class_='dohod-description-info_data tes')

    # Извлечение текста из каждого найденного элемента
    texts = [p for p in (elem.find_all('p') for elem in elements) if p != []]

    i = 0
    # Вывод результатов
    for text in texts:
        for p in text:
            status = p.get_text()

            if status:
                if "акра" in status.lower():
                    res['akra'] = get_status(status)
                elif "эксперт" in status.lower():
                    res['expert'] = get_status(status)
                elif i == 0:
                    res['dohod'] = get_status(status)
                else:
                    res['other'] = status
                i += 1
    return res