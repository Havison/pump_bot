import json

from pybit.unified_trading import HTTP
from binance.client import Client
from config_data.config import Config, load_config
from database.database import (db_bybit_smbl, user_id, db_result_long, db_result_short,
                               long_interval_user, db_bybit, quantity, clear_quantity_signal,
                               db_quantity_selection, premium_user, db_binance_smbl, db_binance, long_interval_user_binance)

from handlers.user import message_long, message_short, message_short_binance, message_long_binance



config: Config = load_config('.env')

session = HTTP(
    testnet=False,
    api_key=config.by_bit.api_key,
    api_secret=config.by_bit.api_secret,
)

client = Client(config.binance_key.api_key, config.binance_key.api_secret, testnet=False)
symbols = [symbol['symbol'] for symbol in client.get_all_tickers() if 'USDT' in symbol['symbol']]


async def symbol_bybit():
    data = session.get_tickers(category="linear")
    for dicts in data['result']['list']:
        if 'USDT' in dicts['symbol']:
            await db_bybit_smbl(dicts['symbol'])
            await db_bybit(dicts['symbol'], dicts['lastPrice'], dicts['openInterest'], dicts['volume24h'])
            last_price = dicts["lastPrice"]
            user = await user_id()
            tg_id = [i[0] for i in user]
            for idt in tg_id:
                premium = await premium_user(idt)
                if not premium:
                    continue
                changes_long, interval_long = await db_result_long(idt)
                changes_short, interval_short = await db_result_short(idt)
                user_price_interval_a = await long_interval_user(interval_long, dicts['symbol'])
                user_price_interval_b = await long_interval_user(interval_short, dicts['symbol'])
                for i in user_price_interval_a:
                    a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if a > changes_long:
                        if await quantity(idt, dicts['symbol'], interval_long, 'bybit', 1):
                            q = await clear_quantity_signal(idt, dicts['symbol'], 'bybit', 1)
                            qi = await db_quantity_selection(idt)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_long(idt, a, dicts['symbol'], interval_long, q, qi_text[qi[1]])
                for i in user_price_interval_b:
                    b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                    if b < changes_short:
                        if await quantity(idt, dicts['symbol'], interval_short, 'bybit', 0):
                            q = await clear_quantity_signal(idt, dicts['symbol'], 'bybit', 0)
                            qi = await db_quantity_selection(idt)
                            qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                            await message_short(idt, b, dicts['symbol'], interval_short, q, qi_text[qi[1]])



async def symbol_binance():
    symbols = [symbol['symbol'] for symbol in client.get_all_tickers() if 'USDT' in symbol['symbol']]
    for dicts in symbols:
        try:
            last_price = client.futures_mark_price(symbol=dicts)['markPrice']
            open_inters = client.futures_open_interest(symbol=dicts)['openInterest']
            volume = client.futures_ticker(symbol=dicts)['volume']
        except:
            continue
        await db_binance_smbl(dicts)
        await db_binance(dicts, last_price, open_inters, volume)
        user = await user_id()
        tg_id = [i[0] for i in user]
        for idt in tg_id:
            premium = await premium_user(idt)
            if not premium:
                continue
            changes_long, interval_long = await db_result_long(idt)
            changes_short, interval_short = await db_result_short(idt)
            user_price_interval_a = await long_interval_user_binance(interval_long, dicts)
            user_price_interval_b = await long_interval_user_binance(interval_short, dicts)
            for i in user_price_interval_a:
                a = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                if a > changes_long:
                    if await quantity(idt, dicts, interval_long, 'binance', 1):
                        q = await clear_quantity_signal(idt, dicts, 'binance', 1)
                        qi = await db_quantity_selection(idt)
                        qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                        await message_long_binance(idt, a, dicts, interval_long, q, qi_text[qi[1]])
            for i in user_price_interval_b:
                b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                if b < changes_short:
                    if await quantity(idt, dicts, interval_short,'binance', 0):
                        q = await clear_quantity_signal(idt, dicts, 'binance', 0)
                        qi = await db_quantity_selection(idt)
                        qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                        await message_short_binance(idt, b, dicts, interval_short, q, qi_text[qi[1]])

















