import asyncio
import logging


from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (long_interval_user, quantity, clear_quantity_signal, clear_quantity_signal_binance, long_interval_user_binance, db_bybit, db_binance, quantity_binance)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance, message_long_mini_bybit, message_long_binance_min, message_long_bb, message_short_bb, message_long_mini_bb


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


async def binance():
    client = Client(config.binance_key.api_key, config.binance_key.api_secret, testnet=False)
    data_binance_no_sorted = client.futures_symbol_ticker()
    binance_data = []
    data_binance = sorted(data_binance_no_sorted, key=lambda k: k['symbol'])
    for i in data_binance:
        if 'USDT' in i['symbol']:
            binance_data.append(i['symbol'])
    return binance_data

async def bybit():
    symbol = []
    data = session.get_tickers(category="linear")
    for dicts in data['result']['list']:
        if 'USDT' in dicts['symbol']:
            symbol.append(dicts['symbol'])
    return symbol



async def symbol_bybit():
    try:
        data = session.get_tickers(category="linear")
        bybit_data = []
        for dicts in data['result']['list']:
            if 'USDT' in dicts['symbol']:
                bybit_data.append((dicts['symbol'], dicts['lastPrice'], dicts['openInterest']))
        await db_bybit(bybit_data)
        await signal_bybit(bybit_data)
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_bybit(bybit_data):
    while bybit_data:
        symbol_signal = [user_signal_bybit(-1002392376833, i) for i in bybit_data[:5]]
        await asyncio.gather(*symbol_signal)
        bybit_data = bybit_data[5:]


async def user_signal_bybit(idt, data_symbol):
    symbol = data_symbol[0]
    last_price = data_symbol[1]
    interval_pd = await long_interval_user(30, symbol)
    user_price_interval_mini = await long_interval_user(3, symbol)
    for i in interval_pd:
        a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if a >= 10:
            if await quantity(symbol, 30, 1):
                if symbol in await binance():
                    qp = await clear_quantity_signal(symbol, 30, 1)
                    await quantity_binance(symbol, 30, 1)
                    await clear_quantity_signal_binance(symbol, 30, 1)
                    await message_long_bb(idt, a, symbol, qp)
                else:
                    qp = await clear_quantity_signal(symbol, 30, 1)
                    await message_long(idt, a, symbol, qp)
        if a <= -10:
            if await quantity(symbol, 30, 0):
                if symbol in await binance():
                    qp = await clear_quantity_signal(symbol, 30, 0)
                    await quantity_binance(symbol, 30, 1)
                    await clear_quantity_signal_binance(symbol, 30, 0)
                    await message_short_bb(idt, a, symbol, qp)
                else:
                    qp = await clear_quantity_signal(symbol, 30, 0)
                    await message_short(idt, a, symbol, qp)
    for i in user_price_interval_mini:
        c = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if c >= 3:
            if await quantity(symbol, 3, 3):
                if symbol in await binance():
                    qp = await clear_quantity_signal(symbol, 3, 3)
                    await quantity_binance(symbol, 3, 3)
                    await clear_quantity_signal_binance(symbol, 3, 3)
                    await message_long_mini_bb(idt, c, symbol, qp)
                else:
                    qp = await clear_quantity_signal(symbol, 3, 3)
                    await message_long_mini_bybit(idt, c, symbol, qp)


async def symbol_binance():
    try:
        client = Client(config.binance_key.api_key, config.binance_key.api_secret, testnet=False)
        data_binance_no_sorted = client.futures_symbol_ticker()
        binance_data = []
        data_binance = sorted(data_binance_no_sorted, key=lambda k: k['symbol'])
        for symbol in data_binance:
            if 'USDT' in symbol['symbol']:
                binance_data.append((symbol['symbol'], symbol['price']))
        await db_binance(binance_data)
        await signal_binance(-10023923768339, binance_data)
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_binance(idt, binance_data):
    while binance_data:
        symbol_signal = [user_binance_signal(idt, i) for i in binance_data[:5]]
        await asyncio.gather(*symbol_signal)
        binance_data = binance_data[5:]


async def user_binance_signal(idt, data_b):
    symbol = data_b[0]
    last_price = data_b[1]
    user_price_interval = await long_interval_user_binance(30, symbol)
    user_price_interval_mini = await long_interval_user_binance(3, symbol)
    for i in user_price_interval:
        a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if a >= 10:
            x = await quantity_binance(symbol, 30, 1)
            if x:
                if symbol in await bybit():
                    qp = await clear_quantity_signal_binance(symbol, 30, 1)
                    await quantity(symbol, 30, 1)
                    await clear_quantity_signal(symbol, 30, 1)
                    await message_long_bb(idt, a, symbol, qp)
                else:
                    q = await clear_quantity_signal_binance(symbol, 30, 1)
                    await message_long_binance(idt, a, symbol, q)
        if a <= -10:
            x = await quantity_binance(symbol, 30, 0)
            if x:
                if symbol in await bybit():
                    qp = await clear_quantity_signal_binance(symbol, 30, 0)
                    await quantity(symbol, 30, 1)
                    await clear_quantity_signal(symbol, 30, 0)
                    await message_short_bb(idt, a, symbol, qp)
                else:
                    q = await clear_quantity_signal_binance(symbol, 30, 0)
                    await message_short_binance(idt, a, symbol, q)
    for i in user_price_interval_mini:
        c = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if c >= 3:
            x = await quantity_binance(symbol, 3, 3)
            if x:
                if symbol in await bybit():
                    qp = await clear_quantity_signal_binance(symbol, 3, 3)
                    await quantity(symbol, 3, 3)
                    await clear_quantity_signal(symbol, 3, 3)
                    await message_long_mini_bb(idt, c, symbol, qp)
                else:
                    q = await clear_quantity_signal_binance(symbol, 3, 3)
                    await message_long_binance_min(idt, c, symbol, q)
