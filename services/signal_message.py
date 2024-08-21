import asyncio

import ccxt

from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (user_id, long_interval_user, db_bybit, quantity, clear_quantity_signal, premium_user, db_binance, long_interval_user_binance, db_setting_selection, state_signal)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance

binance_connect = ccxt.binance()



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
        bybit_symbol = []
        bybit_data = []
        for dicts in data['result']['list']:
            if 'USDT' in dicts['symbol']:
                bybit_data.append((dicts['symbol'], dicts['lastPrice'], dicts['openInterest'], dicts['volume24h']))
                if not dicts['symbol'] in bybit_symbol:
                    bybit_symbol.append(dicts['symbol'])
        await db_bybit(bybit_data)
        user = await user_id()
        for data_symbol in bybit_data:
            symbol = data_symbol[0]
            last_price = data_symbol[1]
            tg_id_user = [i[0] for i in user]
            for idt in tg_id_user:
                premium = await premium_user(idt)
                signal_state = await state_signal(idt)
                if not premium:
                    continue
                if not signal_state[0]:
                    continue
                (changes_long, interval_long, changes_short,
                 interval_short, binance, bybit, open_interes,
                 open_interes_interval, changes_long_mini,
                 changes_mini_interval, quantity_setting,
                 quantity_interval) = await db_setting_selection(idt)
                user_price_interval = await long_interval_user(interval_long, symbol)
                if not bybit:
                    continue
                for i in user_price_interval:
                    a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if a > changes_long:
                        if await quantity(idt, symbol, interval_long, 'bybit', 1):
                            q = await clear_quantity_signal(idt, symbol, 'bybit', 1)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_long(idt, a, symbol, interval_long, q, qi_text[quantity_interval])
                for i in user_price_interval:
                    b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if b < changes_short:
                        if await quantity(idt, symbol, interval_short, 'bybit', 0):
                            q = await clear_quantity_signal(idt, symbol, 'bybit', 0)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_short(idt, b, symbol, interval_short, q, qi_text[quantity_interval])
    except:
        await asyncio.sleep(4)


async def symbol_binance():
    await asyncio.sleep(4)
    try:
        data_binance = []
        data_binance = [(symbol['symbol'], symbol['price'], 0, 0) for symbol in client.futures_symbol_ticker() if 'USDT' in symbol['symbol']]
        await db_binance(data_binance)
        user = await user_id()
        for data_b in data_binance:
            symbol = data_b[0]
            #print(client.futures_open_interest(symbol=symbol)) открытый интерес
            last_price = data_b[1]
            tg_id = [i[0] for i in user]
            for idt in tg_id:
                premium = await premium_user(idt)
                signal_state = await state_signal(idt)
                if not premium:
                    continue
                if not signal_state[0]:
                    continue
                (changes_long, interval_long, changes_short,
                 interval_short, binance, bybit, open_interes,
                 open_interes_interval, changes_long_mini,
                 changes_mini_interval, quantity_setting,
                 quantity_interval) = await db_setting_selection(idt)
                user_price_intervabi = await long_interval_user_binance(interval_long, symbol)
                if not binance:
                    continue
                for i in user_price_intervabi:
                    a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if a > changes_long:
                        if await quantity(idt, symbol, interval_long, 'binance', 1):
                            q = await clear_quantity_signal(idt, symbol, 'binance', 1)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_long_binance(idt, a, symbol, interval_long, q, qi_text[quantity_interval])
                for i in user_price_intervabi:
                    b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if b < changes_short:
                        if await quantity(idt, symbol, interval_short, 'binance', 0):
                            q = await clear_quantity_signal(idt, symbol, 'binance', 0)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_short_binance(idt, b, symbol, interval_short, q, qi_text[quantity_interval])
    except:
        await asyncio.sleep(4)

















