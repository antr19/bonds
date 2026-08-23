import asyncio
import logging
import os
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaDocument
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector

# Настройки логирования для вывода ошибок
logging.basicConfig(level=logging.INFO)

# Ваши данные
BOT_TOKEN = os.getenv("AIOGRAM_TOKEN")
# Для канала можно использовать @username или числовой ID (например, -1001234567890)
CHAT_ID = os.getenv("AIOGRAM_CHAT")
PROXY_URL = os.getenv("AIOGRAM_PROXY", default=None)


async def send_data_to_telegram(message, paths):
    # 2. Создаем aiohttp-сессию с этим коннектором
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
    else:
        session = AiohttpSession()

    # 3. Передаем сессию в бота
    bot = Bot(token=BOT_TOKEN, session=session)

    try:
        # 1. Отправка текстового сообщения
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        # Формируем медиагруппу (от 2 до 10 файлов)
        media_group = [ InputMediaDocument(media=FSInputFile(path)) for path in paths]


        # Отправляем альбомом
        await bot.send_media_group(chat_id=CHAT_ID, media=media_group)
        print("Альбом с документами успешно отправлен!")

        logging.info("Сообщения успешно отправлены!")

    except TelegramBadRequest as e:
        logging.error(f"Ошибка Telegram API: {e.message}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        # Обязательно закрываем сессию aiohttp, чтобы не было утечек
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(send_data_to_telegram("Привет-привет", ["../../premium_result.xlsx", "../../short_result.xlsx"]))