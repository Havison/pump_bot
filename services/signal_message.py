import asyncio
import logging


from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (long_interval_user, quantity, clear_quantity_signal, clear_quantity_signal_binance, long_interval_user_binance, db_setting_selection, state_signal, db_bybit, db_binance, list_premium, quantity_binance)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance, message_long_mini_bybit, message_long_binance_min


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
        user = await list_premium()
        user_iter = [i[0] for i in user]
        while user_iter:
            tg_id_user = [signal_bybit(user, bybit_data) for user in user_iter[:10]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[10:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_bybit(idt, bybit_data):
    while bybit_data:
        symbol_signal = [user_signal_bybit(idt, i) for i in bybit_data[:5]]
        await asyncio.gather(*symbol_signal)
        bybit_data = bybit_data[5:]


async def user_signal_bybit(idt, data_symbol):
    quintity_long = 0
    quintity_short = 0
    quintity_long_mini = 0
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
    user_price_interval_mini = await long_interval_user(setting['intarval_pump_min'], symbol)
    for i in user_price_interval:
        a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if a >= setting['quantity_pump']:
            if await quantity(idt, symbol, setting['interval_pump'], 'bybit', 1):
                q = await clear_quantity_signal(idt, symbol, 'bybit', 1)
                qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_long(idt, a, symbol, setting['interval_pump'], q,
                                   qi_text[setting['interval_signal_pd']])
                quintity_long += 1
                await asyncio.sleep(1)
                if quintity_long > 5:
                    return

    for i in user_price_interval_short:
        b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if b <= setting['quantity_short']:
            if await quantity(idt, symbol, setting['intarval_short'], 'bybit', 0):
                q = await clear_quantity_signal(idt, symbol, 'bybit', 0)
                qi_text = {3: 'За 24 часа', 30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_short(idt, b, symbol, setting['intarval_short'], q,
                                    qi_text[setting['interval_signal_pd']])
                quintity_short += 1
                await asyncio.sleep(1)
                if quintity_short > 5:
                    return

    for i in user_price_interval_mini:
        c = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if c >= setting['quatity_pump_min']:
            if await quantity(idt, symbol, setting['intarval_pump_min'], 'bybit', 3):
                q = await clear_quantity_signal(idt, symbol, 'bybit', 3)
                qi_text = {3: 'За 24 часа', 30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_long_mini_bybit(idt, c, symbol, setting['intarval_pump_min'], q,
                                   qi_text[setting['intarval_signal_pm']])
                quintity_long_mini += 1
                await asyncio.sleep(1)
                if quintity_long_mini > 5:
                    return


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
        user = await list_premium()
        user_iter = [i[0] for i in user]
        while user_iter:
            tg_id_user = [signal_binance(user, binance_data) for user in user_iter[:10]]
            await asyncio.gather(*tg_id_user)
            user_iter = user_iter[10:]
    except Exception as e:
        logger2.error(e)
        await asyncio.sleep(4)


async def signal_binance(idt, binance_data):
    while binance_data:
        symbol_signal = [user_binance_signal(idt, i) for i in binance_data[:5]]
        await asyncio.gather(*symbol_signal)
        binance_data = binance_data[5:]


async def user_binance_signal(idt, data_b):
    quintity_long = 0
    quintity_short = 0
    quintity_long_mini = 0
    setting = await db_setting_selection(idt)
    signal_state = await state_signal(idt)
    symbol = data_b[0]
    last_price = data_b[1]
    if not signal_state[0]:
        return
    if not setting['binance']:
        return
    user_price_interval = await long_interval_user_binance(setting['interval_pump'], symbol)
    user_price_interval_short = await long_interval_user_binance(setting['intarval_short'], symbol)
    user_price_interval_mini = await long_interval_user_binance(setting['intarval_pump_min'], symbol)

    for i in user_price_interval:
        a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if a >= setting['quantity_pump']:
            x = await quantity_binance(idt, symbol, setting['interval_pump'], 'binance', 1)
            if x:
                q = await clear_quantity_signal_binance(idt, symbol, 'binance', 1)
                qi_text = {3: 'За 24 часа', 30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_long_binance(idt, a, symbol, setting['interval_pump'], q,
                                           qi_text[setting['interval_signal_pd']])
                quintity_long += 1
                await asyncio.sleep(1)
                if quintity_long > 5:
                    return

    for i in user_price_interval_short:
        b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if b <= setting['quantity_short']:
            x = await quantity_binance(idt, symbol, setting['intarval_short'], 'binance', 0)
            if x:
                q = await clear_quantity_signal_binance(idt, symbol, 'binance', 0)
                qi_text = {3: 'За 24 часа', 30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_short_binance(idt, b, symbol, setting['intarval_short'], q,
                                            qi_text[setting['interval_signal_pd']])
                quintity_short += 1
                await asyncio.sleep(1)
                if quintity_short > 5:
                    return

    for i in user_price_interval_mini:
        c = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
        if c >= setting['quatity_pump_min']:
            x = await quantity_binance(idt, symbol, setting['intarval_pump_min'], 'binance', 3)
            if x:
                q = await clear_quantity_signal_binance(idt, symbol, 'binance', 3)
                qi_text = {3: 'За 24 часа', 30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                await message_long_binance_min(idt, c, symbol, setting['intarval_pump_min'], q,
                                   qi_text[setting['intarval_signal_pm']])
                quintity_long_mini += 1
                await asyncio.sleep(1)
                if quintity_long_mini > 5:
                    return
