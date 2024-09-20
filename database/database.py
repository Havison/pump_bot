import datetime
import pymysql
from config_data.config import Config, load_config


config: Config = load_config('.env')
user = config.database.user
password = config.database.password
host = config.database.host
database = config.database.database_type


try:
    connect_db = pymysql.connect(host=host, user=user, password=password, database=database)
except Exception as e:
    print(e)


async def db_create_user(tg_id, username):
    with connect_db.cursor() as db:
        result = db.execute('''SELECT * FROM users WHERE tg_id=%s''', (tg_id,))
        if not result:
            dt = datetime.datetime.now() + datetime.timedelta(days=3)
            db.execute('''INSERT INTO users (
            tg_id, username, date_prem)
            VALUES (
            %s, %s, %s)''', (
                tg_id, username, dt)
                             )
            db.execute('''INSERT INTO users_settings (tg_id) VALUES (%s)''', (tg_id,))
            connect_db.commit()


async def db_changes_long(tg_id, changes_long):
    with connect_db.cursor() as db:
        db.execute('''UPDATE users_settings SET quantity_pump=%s WHERE tg_id=%s''', (changes_long, tg_id))
        connect_db.commit()


async def db_interval_long(tg_id, interval_long):
    with connect_db.cursor() as db:
        db.execute('''UPDATE users_settings SET interval_pump=%s WHERE tg_id=%s''', (interval_long, tg_id))
        connect_db.commit()


async def db_quantity_setting(tg_id, quantity_setting):
    with connect_db.cursor() as db:
        db.execute('''UPDATE users_settings SET quatity_signal_pd=%s WHERE tg_id=%s''', (quantity_setting, tg_id))
        connect_db.commit()


async def db_quantity_interval(tg_id, quantity_interval):
    with connect_db.cursor() as db:
        db.execute('''UPDATE users_settings SET interval_signal_pd=%s WHERE tg_id=%s''', (quantity_interval, tg_id))
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
        key = ('quantity_pump', 'interval_pump', 'quantity_short', 'intarval_short', 'quatity_pump_min',
               'intarval_pump_min', 'quatity_signal_pd', 'interval_signal_pd', 'quatity_signal_pm',
               'intarval_signal_pm', 'stop_signal', 'tg_id', 'binance', 'bybit')
        result = dict(zip(key, value))
        return result


async def user_id():
    with connect_db.cursor() as db:
        db.execute('''SELECT tg_id, date_prem FROM users''')
        result = db.fetchall()
        return result


async def long_interval_user(interval_long):
    with connect_db.cursor() as db:
        symbol = {}
        added_date = datetime.datetime.now() - datetime.timedelta(minutes=interval_long)
        db.execute('''SELECT symbol, last_prise FROM bybit WHERE date_create>%s ORDER BY date_create''', added_date)
        result = db.fetchall()
        for i in result:
            symbol.setdefault(i[0], []).append(i[1])
        return symbol


async def long_interval_user_binance(interval_long, symbol):
    with connect_db.cursor() as db:
        symbol = {}
        added_date = datetime.datetime.now() - datetime.timedelta(minutes=interval_long)
        db.execute('''SELECT symbol, last_prise FROM binance WHERE date_create>%s ORDER BY date_create''', added_date)
        result = db.fetchall()
        for i in result:
            symbol.setdefault(i[0], []).append(i[1])
        return symbol


async def market_setting(tg_id, market, on_off):
    with connect_db.cursor() as db:
        if market == 'bybit':
            db.execute('''UPDATE users_settings SET bybit=%s WHERE (tg_id=%s)''', (on_off, tg_id))
            connect_db.commit()
        elif market == 'binance':
            db.execute('''UPDATE users_settings SET binance=%s WHERE (tg_id=%s)''', (on_off, tg_id))
            connect_db.commit()


async def quantity(tg_id, symbol, interval_user, market, short):
    with connect_db.cursor() as db:
        db.execute('''SELECT 1 FROM quantity_user_signal WHERE
        tg_id=%s and symbol=%s and market=%s and short=%s''', (tg_id, symbol, market, short))
        symbol_signal = db.fetchone()
        db.execute('''SELECT quatity_signal_pd, interval_signal_pd FROM
                users_settings WHERE tg_id = %s''', tg_id)
        quantity_tg_ig = db.fetchone()
        dt = datetime.datetime.now() - datetime.timedelta(minutes=quantity_tg_ig[1])
        dt_base = datetime.datetime.now() - datetime.timedelta(minutes=interval_user + 1)
        db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
        (tg_id=%s and symbol=%s and date_signal>%s and market=%s and short=%s) ORDER BY date_signal''',
                                          (tg_id, symbol, dt, market, short))
        quantity_count = db.fetchone()
        db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (tg_id=%s and symbol=%s and date_signal>%s and market=%s and short=%s) ORDER BY date_signal''',
                                               (tg_id, symbol, dt_base, market, short))
        quantity_count_base = db.fetchone()
        dt = datetime.datetime.now()
        if symbol_signal is None:
            db.execute('''INSERT INTO quantity_user_signal (tg_id, symbol, date_signal, market, short) VALUES (
            %s, %s, %s, %s, %s)''', (tg_id, symbol, dt, market, short))
            connect_db.commit()
            return True
        elif quantity_count[0] < quantity_tg_ig[0]:
            if quantity_count_base[0] < 1:
                db.execute('''INSERT INTO quantity_user_signal (tg_id, symbol, date_signal, market, short)
                VALUES (%s, %s, %s, %s, %s)''', (tg_id, symbol, dt, market, short))
                connect_db.commit()
                return True
        else:
            return False


async def clear_quantity_signal(tg_id, symbol, market, short):
    with connect_db.cursor() as db:
        dt_cl = datetime.datetime.now() - datetime.timedelta(minutes=1440)
        db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (tg_id=%s and symbol=%s and date_signal>%s and market=%s and short=%s) ORDER BY date_signal''',
                                          (tg_id, symbol, dt_cl, market, short))
        quantity_count = db.fetchone()
        db.execute('''DELETE FROM quantity_user_signal WHERE (
        tg_id=%s and symbol=%s and date_signal<%s and market=%s and short=%s)''',
                         (tg_id, symbol, dt_cl, market, short))
        connect_db.commit()
        return quantity_count[0]


async def premium_user(tg_id):  #функция проверяет на подписку
    with connect_db.cursor() as db:
        today = datetime.datetime.now()
        db.execute('''SELECT date_prem FROM users WHERE (tg_id=%s and date_prem>%s)''',
                                   (tg_id, today))
        premium = db.fetchone()[0]
        if premium is None:
            return False
        else:
            return premium


async def premium_setting(tg_id, days):
    with connect_db.cursor() as db:
        dt = datetime.datetime.now() + datetime.timedelta(days=days)
        db.execute('''UPDATE users SET date_prem=%s) WHERE (tg_id=%s)''',
                         (dt, tg_id))
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



