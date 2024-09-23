import datetime
import aiosqlite
from config_data.config import Config, load_config

config: Config = load_config('.env')
connect_db = config.database.database_type


async def db_start():
    async with aiosqlite.connect(connect_db) as db:
        async with db.execute('''
            CREATE TABLE IF NOT EXISTS binance (
            symbol TEXT,
            last_prise TEXT,
            date_create TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS bybit (
            symbol TEXT,
            last_prise TEXT,
            oi TEXT,
            date_create TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS quantity_user_signal (
            tg_id TEXT,
            symbol TEXT,
            date_signal TEXT,
            market TEXT,
            short INTEGER
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS quantity_user_signal_mini (
            tg_id INTEGER,
            symbol TEXT,
            date_signal TEXT,
            market TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER,
            username TEXT,
            date_prem TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS users_settings (
            tg_id INTEGER,
            quantity_pump INTEGER DEFAULT 10,
            interval_pump INTEGER DEFAULT 30,
            quantity_short INTEGER DEFAULT 10,
            intarval_short INTEGER DEFAULT 30,
            quatity_pump_min INTEGER DEFAULT 3,
            intarval_pump_min INTEGER DEFAULT 3,
            quatity_signal_pd INTEGER DEFAULT 1,
            interval_signal_pd INTEGER DEFAULT 30,
            quatity_signal_pm INTEGER DEFAULT 1,
            intarval_signal_pm INTEGER DEFAULT 3,
            stop_signal INTEGER DEFAULT 1,
            binance INTEGER DEFAULT 1,
            bybit INTEGER DEFAULT 1
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS setting_oi (
            tg_id INTEGER,
            quantity_oi INTEGER DEFAULT 3,
            interval_oi INTEGER DEFAULT 20,
            quantity_signal INTEGER DEFAULT 1,
            interval_signal INTEGER DEFAULT 20,
            stop_signal INTEGER DEFAULT 1
            )
            ''') as cursor: pass


async def db_bybit(symbol):
    async with aiosqlite.connect(connect_db) as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM bybit WHERE date_create<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO bybit(
        symbol, last_prise, oi, date_create) VALUES (
        ?, ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def db_binance(symbol):
    async with aiosqlite.connect(connect_db) as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM binance WHERE date_create<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO binance(
        symbol, last_prise, date_create) VALUES (
        ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def db_create_user(tg_id, username):
    async with aiosqlite.connect(connect_db) as db:
        await db.commit()
        result = await db.execute('''SELECT * FROM users WHERE tg_id=?''', (tg_id,))
        result = await result.fetchone()
        if not result:
            dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
            await db.execute('''INSERT INTO users (
            tg_id, username, date_prem)
            VALUES (
            ?, ?, ?)''', (
                tg_id, username, dt)
                             )
            await db.execute('''INSERT INTO users_settings (tg_id) VALUES (?)''', (tg_id,))
            await db.commit()
            await db.execute('''INSERT INTO setting_oi (tg_id) VALUES (?)''', (tg_id,))
            await db.commit()


async def db_changes_long(tg_id, changes_long):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET quantity_pump=? WHERE tg_id=?''', (changes_long, tg_id))
        await db.commit()


async def db_interval_long(tg_id, interval_long):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET interval_pump=? WHERE tg_id=?''', (interval_long, tg_id))
        await db.commit()


async def db_quantity_setting(tg_id, quantity_setting):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET quatity_signal_pd=? WHERE tg_id=?''', (quantity_setting, tg_id))
        await db.commit()


async def db_quantity_interval(tg_id, quantity_interval):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET interval_signal_pd=? WHERE tg_id=?''', (quantity_interval, tg_id))
        await db.commit()


async def db_changes_short(tg_id, changes_short):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET quantity_short=? WHERE tg_id=?''', (changes_short, tg_id))
        await db.commit()


async def db_interval_short(tg_id, interval_short):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET intarval_short=? WHERE tg_id=?''', (interval_short, tg_id))
        await db.commit()


async def db_setting_selection(tg_id):
    async with aiosqlite.connect(connect_db) as db:
        value = await db.execute('''SELECT * FROM users_settings WHERE tg_id=?''', (tg_id, ))
        value = await value.fetchone()

        key = ('tg_id', 'quantity_pump', 'interval_pump', 'quantity_short', 'intarval_short', 'quatity_pump_min',
               'intarval_pump_min', 'quatity_signal_pd', 'interval_signal_pd', 'quatity_signal_pm',
               'intarval_signal_pm', 'stop_signal', 'binance', 'bybit')
        result = dict(zip(key, value))
        return result


async def user_id():
    async with aiosqlite.connect(connect_db) as db:
        result = await db.execute('''SELECT tg_id, date_prem FROM users''')
        result = await result.fetchall()
        return result


async def long_interval_user(interval_long, symbol):
    async with aiosqlite.connect(connect_db) as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT last_prise FROM 
        bybit WHERE date_create>? and symbol=? ORDER BY date_create''', (added_date, symbol))
        result = await result.fetchall()
        return result


async def long_interval_user_binance(interval_long, symbol):
    async with aiosqlite.connect(connect_db) as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT last_prise FROM 
        binance WHERE date_create>? and symbol=? ORDER BY date_create''', (added_date, symbol))
        result = await result.fetchall()
        return result


async def market_setting(tg_id, market, on_off):
    async with aiosqlite.connect(connect_db) as db:
        if market == 'bybit':
            await db.execute('''UPDATE users_settings SET bybit=? WHERE (tg_id=?)''', (on_off, tg_id))
            await db.commit()
        elif market == 'binance':
            await db.execute('''UPDATE users_settings SET binance=? WHERE (tg_id=?)''', (on_off, tg_id))
            await db.commit()


async def quantity(tg_id, symbol, interval_user, market, short):
    async with aiosqlite.connect(connect_db) as db:
        symbol_signal = await db.execute('''SELECT 1 FROM quantity_user_signal WHERE
        tg_id=? and symbol=? and market=? and short=?''', (tg_id, symbol, market, short))
        symbol_signal = await symbol_signal.fetchone()
        setting = await db_setting_selection(tg_id)
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=setting['interval_signal_pd'])
        dt_base = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_user + 1)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
        (tg_id=? and symbol=? and date_signal>? and market=? and short=?) ORDER BY date_signal''',
                                          (tg_id, symbol, dt, market, short))
        quantity_count = await quantity_count.fetchone()
        quantity_count_base = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (tg_id=? and symbol=? and date_signal>? and market=? and short=?) ORDER BY date_signal''',
                                               (tg_id, symbol, dt_base, market, short))
        quantity_count_base = await quantity_count_base.fetchone()
        dt = datetime.datetime.now(datetime.timezone.utc)
        if symbol_signal is None:
            await db.execute('''INSERT INTO quantity_user_signal (tg_id, symbol, date_signal, market, short) VALUES (
            ?, ?, ?, ?, ?)''', (tg_id, symbol, dt, market, short))
            await db.commit()
            return True
        elif quantity_count[0] < setting['quatity_signal_pd']:
            if quantity_count_base[0] < 1:
                await db.execute('''INSERT INTO quantity_user_signal (tg_id, symbol, date_signal, market, short)
                VALUES (?, ?, ?, ?, ?)''', (tg_id, symbol, dt, market, short))
                await db.commit()
                return True
        else:
            return False


async def clear_quantity_signal(tg_id, symbol, market, short):
    async with aiosqlite.connect(connect_db) as db:
        dt_cl = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1440)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (tg_id=? and symbol=? and date_signal>? and market=? and short=?) ORDER BY date_signal''',
                                          (tg_id, symbol, dt_cl, market, short))
        quantity_count = await quantity_count.fetchone()
        await db.execute('''DELETE FROM quantity_user_signal WHERE (
        tg_id=? and symbol=? and date_signal<? and market=? and short=?)''',
                         (tg_id, symbol, dt_cl, market, short))
        await db.commit()
        return quantity_count[0]


async def premium_user(tg_id):  #функция проверяет на подписку
    async with aiosqlite.connect(connect_db) as db:
        await db.commit()
        today = datetime.datetime.now(datetime.timezone.utc)
        premium = await db.execute('''SELECT date_prem FROM users WHERE (tg_id=? and date_prem>?)''',
                                   (tg_id, today))
        premium = await premium.fetchone()
        if premium is None:
            return False
        else:
            return premium[0]


async def premium_setting(tg_id, days):
    async with aiosqlite.connect(connect_db) as db:
        dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
        await db.execute('''UPDATE users SET date_prem=? WHERE (tg_id=?)''', (dt, tg_id))
        await db.commit()


async def stop_signal(tg_id, state):
    async with aiosqlite.connect(connect_db) as db:
        await db.execute('''UPDATE users_settings SET stop_signal=? WHERE (tg_id=?)''', (state, tg_id))
        await db.commit()


async def state_signal(tg_id):
    async with aiosqlite.connect(connect_db) as db:
        state_signal_user = await db.execute('''SELECT stop_signal FROM users_settings WHERE (tg_id=?)''',
                                   (tg_id, ))
        state_signal_user = await state_signal_user.fetchone()
        return state_signal_user