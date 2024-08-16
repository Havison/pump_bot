from pybit.unified_trading import HTTP
from config_data.config import Config, load_config
from database.database import (db_bybit_smbl, user_id, db_result_long, db_result_short,
                               long_interval_user, db_bybit, quantity, clear_quantity_signal,
                               db_quantity_selection, premium_user)

from handlers.user import message_long, message_short



config: Config = load_config('.env')

session = HTTP(
    testnet=False,
    api_key=config.by_bit.api_key,
    api_secret=config.by_bit.api_secret,
)


async def symbol_bybit():
    data = session.get_tickers(category="linear")
    for dicts in data['result']['list']:
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
                    if await quantity(idt, dicts['symbol'], interval_long):
                        q = await clear_quantity_signal(idt, dicts['symbol'])
                        qi = await db_quantity_selection(idt)
                        qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                        await message_long(idt, a, dicts['symbol'], interval_long, q, qi_text[qi[1]])
            for i in user_price_interval_b:
                b = eval(f'({last_price} - {i[0]}) / {last_price} * 100')
                if b < changes_short:
                    if await quantity(idt, dicts['symbol'], interval_short):
                        q = await clear_quantity_signal(idt, dicts['symbol'])
                        qi = await db_quantity_selection(idt)
                        qi_text = {30: 'За 24 часа', 360: 'За 6 часов', 720: 'За 12 часов', 1440: 'За 24 часа'}
                        await message_short(idt, b, dicts['symbol'], interval_short, q, qi_text[qi[1]])
















