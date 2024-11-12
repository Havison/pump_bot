import datetime
import pymysql
import aiosqlite
from config_data.config import Config, load_config


async def db_start():
    async with aiosqlite.connect('database/database.db') as db:
        async with db.execute('''
            CREATE TABLE IF NOT EXISTS price (
            symbol TEXT,
            last_prise TEXT,
            date_create TEXT
            )
            ''') as cursor: pass


config: Config = load_config('.env')
user = config.database.user
password = config.database.password
host = config.database.host
database = config.database.database_type


try:
    connect_db = pymysql.connect(host=host, user=user, password=password, database=database)
    print('Connected to MySQL')



    async def db_bybit(symbol):
        async with aiosqlite.connect('database/database.db') as db:
            dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=120)
            await db.execute('''DELETE FROM price WHERE date_create<?''', (dt,))
            await db.commit()
            await db.executemany('''INSERT INTO price(
            symbol, last_prise, date_create) VALUES (
            ?, ?, datetime('now'))''', symbol)
            await db.commit()


    async def db_create_user(tg_id, username):
        with connect_db.cursor() as db:
            db.execute('''SELECT * FROM users WHERE tg_id=%s''', (tg_id,))
            result = db.fetchone()
            if not result:
                dt = datetime.datetime.now()
                db.execute('''INSERT INTO users (
                tg_id, username, date_prem)
                VALUES (
                %s, %s, %s)''', (
                    tg_id, username, dt)
                           )
                connect_db.commit()


    async def db_changes_long(tg_id, changes_long):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET quantity_pump=%s WHERE tg_id=%s''', (changes_long, tg_id))
            connect_db.commit()


    async def db_interval_long(tg_id, interval_long):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET interval_pump=%s WHERE tg_id=%s''', (interval_long, tg_id))
            connect_db.commit()


    async def db_changes_long_min(tg_id, changes_long_min):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET quatity_pump_min=%s WHERE tg_id=%s''', (changes_long_min, tg_id))
            connect_db.commit()


    async def db_interval_long_min(tg_id, interval_long_min):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET intarval_pump_min=%s WHERE tg_id=%s''', (interval_long_min, tg_id))
            connect_db.commit()


    async def db_quantity_setting(tg_id, quantity_setting):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET quatity_signal_pd=%s WHERE tg_id=%s''', (quantity_setting, tg_id))
            connect_db.commit()


    async def db_quantity_interval(tg_id, quantity_interval):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET interval_signal_pd=%s WHERE tg_id=%s''', (quantity_interval, tg_id))
            connect_db.commit()


    async def db_quantity_setting_min(tg_id, quantity_setting):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET quatity_signal_pm=%s WHERE tg_id=%s''', (quantity_setting, tg_id))
            connect_db.commit()


    async def db_quantity_interval_min(tg_id, quantity_interval):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET intarval_signal_pm=%s WHERE tg_id=%s''', (quantity_interval, tg_id))
            connect_db.commit()


    async def db_changes_short(tg_id, changes_short):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET quantity_short=%s WHERE tg_id=%s''', (changes_short, tg_id))
            connect_db.commit()


    async def db_interval_short(tg_id, interval_short):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET intarval_short=%s WHERE tg_id=%s''', (interval_short, tg_id))
            connect_db.commit()


    async def db_setting_selection(tg_id):
        with connect_db.cursor() as db:
            db.execute('''SELECT * FROM users_settings WHERE tg_id=%s''', tg_id)
            value = db.fetchone()
            key = ('quantity_pump', 'interval_pump', 'quantity_short', 'interval_short', 'quantity_pump_min',
                   'interval_pump_min', 'quantity_signal_pd', 'interval_signal_pd', 'quantity_signal_pm',
                   'interval_signal_pm', 'stop_signal', 'tg_id', 'binance', 'bybit')
            result = dict(zip(key, value))
            return result


    async def db_setting_selection_all():
        with connect_db.cursor() as db:
            db.execute('''SELECT * FROM users_settings''')
            value = db.fetchall()
            users = {}
            key = ('quantity_pump', 'interval_pump', 'quantity_short', 'interval_short', 'quantity_pump_min',
                   'interval_pump_min', 'quantity_signal_pd', 'interval_signal_pd', 'quantity_signal_pm',
                   'interval_signal_pm', 'stop_signal', 'tg_id', 'binance', 'bybit')
            for i in value:
                users[i[11]] = dict(zip(key, i))
            return users


    async def user_id():
        with connect_db.cursor() as db:
            db.execute('''SELECT tg_id, date_prem FROM users''')
            result = db.fetchall()
            return result


    async def symbol_binance_bybit():
        with connect_db.cursor() as db:
            db.execute('''SELECT symbol, market FROM symbol''')
            result = db.fetchall()
            bybit = []
            binance = []
            for i in result:
                if i[1] == 1:
                    bybit.append(i[0])
                else:
                    binance.append(i[0])
            market = (bybit, binance)
            return market


    async def db_symbol_create(symbol_list):
        with connect_db.cursor() as db_sql:
            for symbol in symbol_list:
                db_sql.execute('''SELECT * FROM symbol WHERE symbol = %s AND market = %s''', (symbol[0], symbol[1]))
                result = db_sql.fetchone()
                if not result:
                    db_sql.execute('''INSERT INTO symbol(symbol, market) VALUES (%s, %s)''', (symbol[0], symbol[1]))
            connect_db.commit()


    async def long_interval_user(interval_long):
        async with aiosqlite.connect('database/database.db') as db:
            added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
            result = await db.execute('''SELECT symbol, last_prise FROM 
            price WHERE date_create>? ORDER BY date_create''', (added_date, ))
            result = await result.fetchall()
            result_symbol = {}
            for key, value in result:
                result_symbol.setdefault(key, []).append(value)
            return result_symbol


    async def market_setting(tg_id, market, on_off):
        with connect_db.cursor() as db:
            if market == 'bybit':
                db.execute('''UPDATE users_settings SET bybit=%s WHERE (tg_id=%s)''', (on_off, tg_id))
                connect_db.commit()
            elif market == 'binance':
                db.execute('''UPDATE users_settings SET binance=%s WHERE (tg_id=%s)''', (on_off, tg_id))
                connect_db.commit()


    async def quantity(tg_id, symbol, interval_user, short, interval_signal, quantity_signal):
        with connect_db.cursor() as db:
            db.execute('''SELECT 1 FROM quantity WHERE
            tg_id=%s and symbol=%s and pd=%s''', (tg_id, symbol, short))
            symbol_signal = db.fetchone()
            dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_signal)
            dt_base = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_user + 1)
            db.execute('''SELECT COUNT(*) FROM quantity WHERE (
            tg_id=%s and symbol=%s and pd=%s and date>%s) ORDER BY date''', (tg_id, symbol, short, dt))
            quantity_count = db.fetchone()
            db.execute('''SELECT COUNT(*) FROM quantity WHERE (
            tg_id=%s and symbol=%s and pd=%s and date>%s) ORDER BY date''', (tg_id, symbol, short, dt_base))
            quantity_count_base = db.fetchone()
            dt = datetime.datetime.now(datetime.timezone.utc)
            if symbol_signal is None:
                db.execute('''INSERT INTO quantity (tg_id, symbol, pd, date) VALUES (
                %s, %s, %s, %s)''', (tg_id, symbol, short, dt))
                connect_db.commit()
                return True
            elif quantity_count[0] < quantity_signal:
                if quantity_count_base[0] < 1:
                    db.execute('''INSERT INTO quantity (tg_id, symbol, pd, date)
                    VALUES (%s, %s, %s, %s)''', (tg_id, symbol, short, dt))
                    connect_db.commit()
                    return True
            else:
                return False


    async def clear_quantity_signal(tg_id, symbol, short, interval_signal):
        with connect_db.cursor() as db:
            if interval_signal not in [360, 720]:
                interval_signal = 1440
            dt_cl = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_signal)
            db.execute('''SELECT COUNT(*) FROM quantity WHERE
                    (tg_id=%s and symbol=%s and pd=%s and date>%s) ORDER BY date''',
                                              (tg_id, symbol, short, dt_cl))
            quantity_count = db.fetchone()
            dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1440)
            db.execute('''DELETE FROM quantity WHERE (
            tg_id=%s and symbol=%s and pd=%s and date<%s)''',
                             (tg_id, symbol, short, dt))
            connect_db.commit()
            return quantity_count[0]


    async def premium_user(tg_id):  #функция проверяет на подписку
        with connect_db.cursor() as db:
            connect_db.commit()
            db.execute('''SELECT tg_id, data_prem FROM users_prem WHERE (tg_id=%s)''',
                                       (tg_id, ))
            premium = db.fetchone()
            if premium:
                return premium[1]
            else:
                return False


    async def list_premium():
        with connect_db.cursor() as db:
            await clear_premium()
            connect_db.commit()
            db.execute('''SELECT tg_id FROM users_prem''')
            users = db.fetchall()
            return users


    async def free_premium_user(tg_id):
        with connect_db.cursor() as db:
            connect_db.commit()
            db.execute('''SELECT tg_id FROM free_prem WHERE tg_id=%s''', (tg_id, ))
            free_premium = db.fetchone()
            if free_premium:
                return True
            else:
                db.execute('''INSERT INTO free_prem (tg_id) VALUES (%s)''', (tg_id,))
                connect_db.commit()
                await premium_setting(tg_id, 1)
                return False


    async def clear_premium():
        with connect_db.cursor() as db:
            connect_db.commit()
            today = datetime.datetime.now()
            db.execute('''SELECT tg_id FROM users_prem WHERE (data_prem<%s)''',
                                       (today, ))
            premium = db.fetchall()
            if premium:
                for i in premium:
                    db.execute('''DELETE FROM users_prem WHERE tg_id=%s''', (i,))
                    connect_db.commit()
                    db.execute('''DELETE FROM users_settings WHERE tg_id=%s''', (i,))
                    connect_db.commit()
                    db.execute('''DELETE FROM setting_oi WHERE tg_id=%s''', (i,))
                    connect_db.commit()


    async def premium_setting(tg_id, days):
        with connect_db.cursor() as db:
            db.execute('''SELECT tg_id, data_prem FROM users_prem WHERE (tg_id=%s)''', (tg_id, ))
            premium = db.fetchone()
            if premium:
                dt = premium[1] + datetime.timedelta(days=days)
                db.execute('''UPDATE users_prem SET date_prem=%s WHERE (tg_id=%s)''', (dt, tg_id))
                connect_db.commit()
            else:
                dt = datetime.datetime.now() + datetime.timedelta(days=days)
                db.execute('''INSERT INTO users_prem (tg_id, data_prem) VALUES (%s, %s)''', (tg_id, dt))
                connect_db.commit()
                db.execute('''INSERT INTO users_settings (tg_id) VALUES (%s)''', (tg_id,))
                connect_db.commit()
                db.execute('''INSERT INTO setting_oi (tg_id) VALUES (%s)''', (tg_id,))
                connect_db.commit()


    async def stop_signal(tg_id, state):
        with connect_db.cursor() as db:
            db.execute('''UPDATE users_settings SET stop_signal=%s WHERE (tg_id=%s)''', (state, tg_id))
            connect_db.commit()


    async def state_signal(tg_id):
        with connect_db.cursor() as db:
            db.execute('''SELECT stop_signal FROM users_settings WHERE (tg_id=%s)''',
                                       (tg_id, ))
            state_signal_user = db.fetchone()
            return state_signal_user

except Exception as e:
    print(e)
    connect_db = pymysql.connect(host=host, user=user, password=password, database=database)