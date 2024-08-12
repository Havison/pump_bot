from pybit.unified_trading import HTTP
import humanize
from config_data.config import Config, load_config
from database.database import db_bybit_smbl, db_bybit
import datetime
_i = humanize.i18n.activate('ru_RU')

config: Config = load_config('.env')

session = HTTP(
    testnet=False,
    api_key=config.by_bit.api_key,
    api_secret=config.by_bit.api_secret,
)


async def symbol_bybit():
    data = session.get_tickers(category="linear")
    for dicts in data['result']['list']:
        db_bybit_smbl(dicts['symbol'])
        db_bybit(dicts['symbol'], dicts["lastPrice"], dicts["openInterest"], dicts["volume24h"])

