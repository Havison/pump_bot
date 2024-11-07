import asyncio
import logging

import requests
from pybit.unified_trading import HTTP
from config_data.config import Config, load_config
from database.database import (long_interval_user, quantity, clear_quantity_signal, db_setting_selection, state_signal, db_bybit, list_premium)
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
                bybit_symbol.append(dicts['symbol'])
        for data in data_binance:
            if 'USDT' in data['symbol']:
                if data['symbol'] not in bybit_symbol:
                    binance_data.append((data['symbol'], data['price']))
                binance_symbol.append(data['symbol'])
        data_list = bybit_data + binance_data
        result = (data_list, bybit_symbol, binance_symbol)
        return result
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(3)
        await market_price()


async def market_add_database():
    data = await market_price()
    await db_bybit(data[0])
    await asyncio.sleep(7)


async def users_list():
    try:
        last_price = await market_price()
        user = await list_premium()
        user_iter = [i[0] for i in user]
        while user_iter:
            tg_id_user = [user_signal_bybit(user, last_price) for user in user_iter[:10]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[10:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def default_signal_user(idt, a, b, symbol, sml, quantity_interval, interval, pd, bybit, binance, quantity_signal_pd, interval_signal):
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
            q = await clear_quantity_signal(idt, symbol, pd, interval_signal)
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
            await asyncio.sleep(1)


async def user_signal_bybit(idt, data_symbol):
    setting = await db_setting_selection(idt)
    quantity_interval = setting['interval_signal_pd']
    quantity_interval_min = setting['interval_signal_pm']
    interval_pump = setting['interval_pump']
    interval_dump = setting['interval_short']
    interval_pump_min = setting['interval_pump_min']
    quantity_signal_pd = setting['quantity_signal_pd']
    quantity_signal_pm = setting['quantity_signal_pm']
    interval_signal = setting['interval_signal_pd']
    interval_signal_min = setting['interval_signal_pm']
    user_price_interval = await long_interval_user(interval_pump)
    user_price_interval_short = await long_interval_user(interval_dump)
    user_price_interval_mini = await long_interval_user(interval_pump_min)
    for i in data_symbol[0]:
        symbol = i[0]
        a_pump = eval(f'({i[1]} - {user_price_interval[symbol]}) / {i[1]} * 100')
        a_dump = eval(f'({i[1]} - {user_price_interval_short[symbol]}) / {i[1]} * 100')
        a_long = eval(f'({i[1]} - {user_price_interval_mini[symbol]}) / {i[1]} * 100')
        b_pump = setting['quantity_pump']
        b_dump = setting['quantity_short']
        b_long = setting['quantity_pump_min']
        await asyncio.gather(default_signal_user(idt, a_pump, b_pump, symbol,
                                                 '&#128994;', quantity_interval, interval_pump,
                                                 1, data_symbol[1], data_symbol[2], quantity_signal_pd, interval_signal),
                             default_signal_user(idt, b_dump, a_dump, symbol,
                                                 '&#128308;', quantity_interval, interval_dump,
                                                 0, data_symbol[1], data_symbol[2], quantity_signal_pd, interval_signal),
                             default_signal_user(idt, a_long, b_long, symbol,
                                                 '&#x1F4B9;', quantity_interval_min, interval_pump_min,
                                                 2, data_symbol[1], data_symbol[2], quantity_signal_pm,
                                                 interval_signal_min)
                             )