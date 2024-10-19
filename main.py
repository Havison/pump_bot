import asyncio
import logging
import tracemalloc

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import user
from config_data.config import Config, load_config
from keyboards.set_menu import set_main_menu
from services.signal_message import symbol_bybit, symbol_binance
from database.database import db_start, db_start_binance

import sentry_sdk


sentry_sdk.init(
    dsn="https://833576debd9b254b6af3a73fda18b5cf@o4507817931571200.ingest.de.sentry.io/4507817934848080",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)


logger = logging.getLogger(__name__)
dp = Dispatcher()
tracemalloc.start()


async def countinues_taks_bybit():
    while True:
        await symbol_bybit()


async def countinues_taks_binance():
    while True:
        await symbol_binance()


async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        filename=f'{__name__}.log',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')
    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config('.env')

    task_bybit = asyncio.create_task(countinues_taks_bybit())
    task_binance = asyncio.create_task(countinues_taks_binance())

    # Инициализируем объект хранилища
    #storage = ...

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


    await set_main_menu(bot)
    await db_start()
    await db_start_binance()


    dp.include_router(user.router)



    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=[], timeout=60)




asyncio.run(main())



# Регистрируем миддлвари
#logger.info('Подключаем миддлвари')
# ...


