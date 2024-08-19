import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import user
from config_data.config import Config, load_config
from keyboards.set_menu import set_main_menu
from database.database import db_start
from services.signal_message import symbol_bybit, symbol_binance

logger = logging.getLogger(__name__)
dp = Dispatcher()
tracemalloc.start()


async def countinues_taks():
    while True:
        await symbol_bybit()
        await symbol_binance()
        await asyncio.sleep(5)


async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')
    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config('.env')

    task = asyncio.create_task(countinues_taks())

    # Инициализируем объект хранилища
    #storage = ...

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


    await set_main_menu(bot)
    await db_start()
    dp.include_router(user.router)



    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=[])




asyncio.run(main())



# Регистрируем миддлвари
#logger.info('Подключаем миддлвари')
# ...
