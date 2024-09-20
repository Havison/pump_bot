import asyncio


import logging
from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (user_id, long_interval_user, quantity, clear_quantity_signal, premium_user, long_interval_user_binance, db_setting_selection, state_signal)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance


logger2 = logging.getLogger(__name__)
handler2 = logging.FileHandler(f"{__name__}.log")
formatter2 = logging.Formatter("%(filename)s:%(lineno)d #%(levelname)-8s "
                               "[%(asctime)s] - %(name)s - %(message)s")
handler2.setFormatter(formatter2)
logger2.addHandler(handler2)
logger2.info(f"Testing the custom logger for module {__name__}")


config: Config = load_config('.env')

session = HTTP(
    testnet=False,
    api_key=config.by_bit.api_key,
    api_secret=config.by_bit.api_secret,
)

client = Client(config.binance_key.api_key, config.binance_key.api_secret, testnet=False)


async def symbol_bybit():
    try:
        await asyncio.sleep(4)
        data = session.get_tickers(category="linear")
        bybit_data = []
        for dicts in data['result']['list']:
            if 'USDT' in dicts['symbol']:
                bybit_data.append((dicts['symbol'], dicts['lastPrice']))
        user = await user_id()
        tg_id_user = [i[0] for i in user]
        for idt in tg_id_user:
            setting = await db_setting_selection(idt)
            if not setting['bybit']:
                continue
            premium = await premium_user(idt)
            if not premium:
                continue
            signal_state = await state_signal(idt)
            if not signal_state[0]:
                continue
            user_price_interval = await long_interval_user(setting['interval_pump'])
            user_price_interval_short = await long_interval_user(setting['intarval_short'])
            for data_symbol in bybit_data:
                symbol = data_symbol[0]
                last_price = data_symbol[1]
                for i in user_price_interval[symbol]:
                    a = eval(f'({last_price} - {i}) / {last_price} * 100')
                    if a >= setting['quantity_pump']:
                        if await quantity(idt, symbol, setting['interval_pump'], 'bybit', 1):
                            q = await clear_quantity_signal(idt, symbol, 'bybit', 1)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_long(idt, a, symbol, setting['interval_pump'], q, qi_text[setting['interval_signal_pd']])
                            await asyncio.sleep(2)
                for i in user_price_interval_short[symbol]:
                    b = eval(f'({last_price} - {i}) / {last_price} * 100')
                    if b <= setting['quantity_short']:
                        if await quantity(idt, symbol, setting['intarval_short'], 'bybit', 0):
                            q = await clear_quantity_signal(idt, symbol, 'bybit', 0)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_short(idt, b, symbol, setting['intarval_short'], q, qi_text[setting['interval_signal_pd']])
                            await asyncio.sleep(2)
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def symbol_binance():
    try:
        await asyncio.sleep(4)
        data_binance = client.futures_symbol_ticker()
        binance_data = []
        for symbol in data_binance:
            if 'USDT' in symbol['symbol']:
                binance_data.append((symbol['symbol'], symbol['price']))
        user = await user_id()
        tg_id_user = [i[0] for i in user]
        for idt in tg_id_user:
            setting = await db_setting_selection(idt)
            premium = await premium_user(idt)
            if not premium:
                continue
            signal_state = await state_signal(idt)
            if not signal_state[0]:
                continue
            if not setting['binance']:
                continue
            user_price_interval = await long_interval_user_binance(setting['interval_pump'])
            user_price_interval_short = await long_interval_user_binance(setting['intarval_short'])
            for data_b in binance_data:
                symbol = data_b[0]
                last_price = data_b[1]
                for i in user_price_interval[symbol]:
                    a = eval(f'({last_price} - {i}) / {last_price} * 100')
                    if a >= setting['quantity_pump']:
                        if await quantity(idt, symbol, setting['interval_pump'], 'binance', 1):
                            q = await clear_quantity_signal(idt, symbol, 'binance', 1)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_long_binance(idt, a, symbol, setting['interval_pump'], q, qi_text[setting['interval_signal_pd']])
                            await asyncio.sleep(2)
                for i in user_price_interval_short[symbol]:
                    b = eval(f'({last_price} - {i}) / {last_price} * 100')
                    if b <= setting['quantity_short']:
                        if await quantity(idt, symbol, setting['intarval_short'], 'binance', 0):
                            q = await clear_quantity_signal(idt, symbol, 'binance', 0)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_short_binance(idt, b, symbol, setting['intarval_short'], q, qi_text[setting['interval_signal_pd']])
                            await asyncio.sleep(2)
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)

















