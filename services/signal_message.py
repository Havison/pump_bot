import asyncio
import logging

import requests
from pybit.unified_trading import HTTP
from config_data.config import Config, load_config
from database.database import (db_symbol_create, symbol_binance_bybit, long_interval_user, quantity,
                               clear_quantity_signal, db_setting_selection, state_signal, db_bybit, list_premium,
                               clear_premium)
from handlers.user import message_bybit_binance, message_bybit, message_binance

logger2 = logging.getLogger(__name__)
handler2 = logging.FileHandler(f"{__name__}.log")
formatter2 = logging.Formatter("%(filename)s:%(lineno)d #%(levelname)-8s "
                               "[%(asctime)s] - %(name)s - %(message)s")

config: Config = load_config('.env')

try:
    session = HTTP(
        testnet=False,
        api_key=config.by_bit.api_key,
        api_secret=config.by_bit.api_secret,
    )
except Exception as e:
    logger2.error(e)


async def market_price():
    try:
        await asyncio.sleep(1)
        url = 'https://fapi.binance.com/fapi/v2/ticker/price'
        response = requests.get(url)
        data_binance = response.json()
        binance_data = []
        binance_symbol = []
        data_bybit = session.get_tickers(category="linear")
        bybit_data = []
        bybit_symbol = []
        for dicts in data_bybit['result']['list']:
            if 'USDT' in dicts['symbol']:
                bybit_data.append((dicts['symbol'], dicts['lastPrice']))
                bybit_symbol.append((dicts['symbol'], 1))
        for data in data_binance:
            if 'USDT' in data['symbol']:
                if data['symbol'] not in bybit_symbol:
                    binance_data.append((data['symbol'], data['price']))
                binance_symbol.append((data['symbol'], 0))
        data_list = bybit_data + binance_data
        result = (data_list, bybit_symbol, binance_symbol)
        return result
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(5)
        await market_price()


async def market_add_database():
    data = await market_price()
    await db_bybit(data[0])
    await clear_premium()
    await asyncio.sleep(5)


async def users_list():
    try:
        bybit, binance = await symbol_binance_bybit()
        user = await list_premium()
        user_iter = [i[0] for i in user]
        while user_iter:
            tg_id_user = [user_signal_bybit(user, bybit, binance) for user in user_iter[:10]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[10:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(2)


async def default_signal_user(idt, a, b, symbol, sml, quantity_interval, interval, pd, bybit, binance,
                              quantity_signal_pd):
    quantity_signal = 0
    hours_signal = {360: 'за 6 часов', 720: 'за 12 часов'}
    signal_state = await state_signal(idt)
    if quantity_interval not in hours_signal:
        hours = 'за 24 часа'
    else:
        hours = hours_signal[quantity_interval]
    if not signal_state[0]:
        return
    if a >= b:
        if await quantity(idt, symbol, interval, pd, quantity_interval, quantity_signal_pd):
            await asyncio.sleep(2)
            q = await clear_quantity_signal(idt, symbol, pd, quantity_interval)
            quantity_signal += 1
            if quantity_signal > 10:
                return
            if pd == 0:
                a, b = b, a
            if symbol in bybit and symbol in binance:
                await message_bybit_binance(idt, a, symbol, interval, q, sml, hours)
            elif symbol in bybit:
                await message_bybit(idt, a, symbol, interval, q, sml, hours)
            else:
                await message_binance(idt, a, symbol, interval, q, sml, hours)


async def user_signal_bybit(idt, bybit, binance):
    setting = await db_setting_selection(idt)
    quantity_interval = setting['interval_signal_pd']
    quantity_interval_min = setting['interval_signal_pm']
    interval_pump = setting['interval_pump']
    interval_dump = setting['interval_short']
    interval_pump_min = setting['interval_pump_min']
    quantity_signal_pd = setting['quantity_signal_pd']
    quantity_signal_pm = setting['quantity_signal_pm']
    user_price_interval = await long_interval_user(interval_pump)
    user_price_interval_short = await long_interval_user(interval_dump)
    user_price_interval_mini = await long_interval_user(interval_pump_min)
    market_symbol = bybit + binance
    for symbol in market_symbol:
        try:
            max_price_pump = eval(user_price_interval[symbol][-1])
            min_price_pump = min(list(map(eval, user_price_interval[symbol])))
            min_price_dump = eval(user_price_interval_short[symbol][-1])
            max_price_dump = max(list(map(eval, user_price_interval_short[symbol])))
            max_price_pump_min = eval(user_price_interval_mini[symbol][-1])
            min_price_pump_min = min(list(map(eval, user_price_interval_mini[symbol])))
            a_pump = (max_price_pump - min_price_pump) / max_price_pump * 100
            a_dump = (min_price_dump - max_price_dump) / min_price_dump * 100
            a_long = (max_price_pump_min - min_price_pump_min) / max_price_pump_min * 100
            b_pump = setting['quantity_pump']
            b_dump = setting['quantity_short']
            b_long = setting['quantity_pump_min']
            await asyncio.gather(default_signal_user(idt, a_pump, b_pump, symbol,
                                                     '&#128994;', quantity_interval, interval_pump,
                                                     1, bybit, binance, quantity_signal_pd),
                                 default_signal_user(idt, b_dump, a_dump, symbol,
                                                     '&#128308;', quantity_interval, interval_dump,
                                                     0, bybit, binance, quantity_signal_pd),
                                 default_signal_user(idt, a_long, b_long, symbol,
                                                     '&#x1F4B9;', quantity_interval_min, interval_pump_min,
                                                     2, bybit, binance, quantity_signal_pm)
                                 )
        except Exception as e:
            logger2.error(e)
            continue


async def add_symbol():
    symbol = await market_price()
    add = symbol[1] + symbol[2]
    await db_symbol_create(add)
