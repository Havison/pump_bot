import asyncio
import logging
from datetime import datetime

from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (user_id, long_interval_user, quantity, clear_quantity_signal, premium_user, long_interval_user_binance, db_setting_selection, state_signal, db_bybit, db_binance)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance


logger2 = logging.getLogger(__name__)
handler2 = logging.FileHandler(f"{__name__}.log")
formatter2 = logging.Formatter("%(filename)s:%(lineno)d #%(levelname)-8s "
                               "[%(asctime)s] - %(name)s - %(message)s")
handler2.setFormatter(formatter2)
logger2.addHandler(handler2)
logger2.info(f"Testing the custom logger for module {__name__}")


config: Config = load_config('.env')

try:
    session = HTTP(
        testnet=False,
        api_key=config.by_bit.api_key,
        api_secret=config.by_bit.api_secret,
    )
except Exception as e:
    logger2.error(e)


async def symbol_bybit():
    try:
        data = session.get_tickers(category="linear")
        bybit_data = []
        for dicts in data['result']['list']:
            if 'USDT' in dicts['symbol']:
                bybit_data.append((dicts['symbol'], dicts['lastPrice'], dicts['openInterest']))
        await db_bybit(bybit_data)
        user = await user_id()
        user_iter = [i[0] for i in user if await premium_user(i[0])]
        while user_iter:
            tg_id_user = [signal_bybit(user, bybit_data) for user in user_iter[:5]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[5:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_bybit(idt, bybit_data):
    while bybit_data:
        symbol_signal = [user_signal_bybit(idt, i) for i in bybit_data[:10]]
        await asyncio.gather(*symbol_signal)
        bybit_data = bybit_data[10:]

async def user_signal_bybit(idt, data_symbol):
    setting = await db_setting_selection(idt)
    signal_state = await state_signal(idt)
    if not signal_state[0]:
        return
    if not setting['bybit']:
        return
    symbol = data_symbol[0]
    last_price = data_symbol[1]
    user_price_interval = await long_interval_user(setting['interval_pump'], symbol)
    user_price_interval_short = await long_interval_user(setting['intarval_short'], symbol)
    for i in user_price_interval:
        a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if a >= setting['quantity_pump']:
            if await quantity(idt, symbol, setting['interval_pump'], 'bybit', 1):
                q = await clear_quantity_signal(idt, symbol, 'bybit', 1)
                qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_long(idt, a, symbol, setting['interval_pump'], q,
                                   qi_text[setting['interval_signal_pd']])
                await asyncio.sleep(1)
    for i in user_price_interval_short:
        b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if b <= setting['quantity_short']:
            if await quantity(idt, symbol, setting['intarval_short'], 'bybit', 0):
                q = await clear_quantity_signal(idt, symbol, 'bybit', 0)
                qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_short(idt, b, symbol, setting['intarval_short'], q,
                                    qi_text[setting['interval_signal_pd']])
                await asyncio.sleep(1)


async def symbol_binance():
    try:
        client = Client(config.binance_key.api_key, config.binance_key.api_secret, testnet=False)
        data_binance = client.futures_symbol_ticker()
        binance_data = []
        for symbol in data_binance:
            if 'USDT' in symbol['symbol']:
                binance_data.append((symbol['symbol'], symbol['price']))
        await db_binance(binance_data)
        user = await user_id()
        user_iter = [i[0] for i in user if await premium_user(i[0])][:30]
        while user_iter:
            tg_id_user = [signal_binance(user, binance_data) for user in user_iter[:5]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[5:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_binance(idt, binance_data):
    for data_b in binance_data:
        setting = await db_setting_selection(idt)
        symbol = data_b[0]
        last_price = data_b[1]
        signal_state = await state_signal(idt)
        if not signal_state[0]:
            continue
        if not setting['binance']:
            return
        user_price_interval = await long_interval_user_binance(setting['interval_pump'], symbol)
        user_price_interval_short = await long_interval_user_binance(setting['intarval_short'], symbol)
        for i in user_price_interval:
            a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
            if a >= setting['quantity_pump']:
                if await quantity(idt, symbol, setting['interval_pump'], 'binance', 1):
                    q = await clear_quantity_signal(idt, symbol, 'binance', 1)
                    qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                    await message_long_binance(idt, a, symbol, setting['interval_pump'], q,
                                               qi_text[setting['interval_signal_pd']])
                    await asyncio.sleep(1)
        for i in user_price_interval_short:
            b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
            if b <= setting['quantity_short']:
                if await quantity(idt, symbol, setting['intarval_short'], 'binance', 0):
                    q = await clear_quantity_signal(idt, symbol, 'binance', 0)
                    qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                    await message_short_binance(idt, b, symbol, setting['intarval_short'], q,
                                                qi_text[setting['interval_signal_pd']])
                    await asyncio.sleep(1)