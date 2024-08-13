import datetime
import aiosqlite


async def db_start():
    async with aiosqlite.connect('database/database.db') as db:
        async with db.execute('''
            CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
        date_of_start TEXT
        )
        ''')
    db.commit()

    cur.execute('''CREATE TABLE IF NOT EXISTS long (
    tg_id INTEGER PRIMARY KEY,
    changes_long INTEGER,
    interval_long INTEGER)''')
    db.commit()

    cur.execute('''CREATE TABLE IF NOT EXISTS short (
    tg_id INTEGER PRIMARY KEY,
    changes_short INTEGER,
    interval_short INTEGER)''')
    db.commit()

    cur.execute('''CREATE TABLE IF NOT EXISTS bybit_symbol (symbol TEXT PRIMARY KEY)''')
    db.commit()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS bybit (
        symbol TEXT,
        lastPrice TEXT,
        openInterest TEXT,
        volume TEXT,
        date_lp TEXT
        )
        ''')
    db.commit()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS symbol_users (
        tg_id INTEGER,
        symbol TEXT,
        date_sgnl TEXT
        )
        ''')
    db.commit()


def db_bybit_smbl(symbol):
    smbl = cur.execute('''SELECT 1 FROM bybit_symbol WHERE symbol=?''',(symbol, )).fetchone()
    if smbl is None:
        cur.execute('''INSERT INTO bybit_symbol(symbol) VALUES (?)''', (symbol, ))
        db.commit()


def db_bybit(symbol, lp, oi, vlm):
    cur.execute('''SELECT COUNT(*) FROM bybit WHERE symbol=?''',(symbol,))
    count = cur.fetchone()[0]
    if count > 4800:
        cur.execute('''DELETE FROM bybit WHERE symbol={key} ORDER BY ROWID LIMIT 1'''.format(key=symbol))
    cur.execute('''INSERT INTO bybit(
    symbol, lastPrice, openInterest, volume, date_lp) VALUES (
    ?, ?, ?, ?, datetime('now'))''', (
        symbol, lp, oi, vlm))
    db.commit()


async def db_create_user(tg_id, username, first_name, last_name):
    result = cur.execute('''SELECT 1 FROM users WHERE tg_id={key}'''.format(key=tg_id)).fetchone()
    if result is None:
        cur.execute('''INSERT INTO users (
        tg_id, username, first_name, last_name, date_of_start) 
        VALUES (
        ?, ?, ?, ?, datetime('now'))''', (
            tg_id, username, first_name, last_name)
                    )
        cur.execute('''INSERT INTO long (
        tg_id, changes_long, interval_long
        )
        VALUES (?, ?, ?)''',(
            tg_id, 10, 30)
                    )
        cur.execute('''INSERT INTO short (
        tg_id, changes_short, interval_short
        )
        VALUES (?, ?, ?)''',(
            tg_id, -10, 30)
                    )
        db.commit()


async def db_changes_long(tg_id, changes_long):
    cur.execute('''UPDATE long SET changes_long=? WHERE tg_id=?''', (changes_long, tg_id))
    db.commit()


async def db_interval_long(tg_id, interval_long):
    cur.execute('''UPDATE long SET interval_long=? WHERE tg_id=?''', (interval_long, tg_id))
    db.commit()


async def db_result_long(tg_id):
    result = cur.execute('''SELECT changes_long, interval_long FROM long WHERE tg_id={key}'''.format(key=tg_id)).fetchone()
    return result


async def db_changes_short(tg_id, changes_short):
    cur.execute('''UPDATE short SET changes_short=? WHERE tg_id=?''', (changes_short, tg_id))
    db.commit()


async def db_interval_short(tg_id, interval_short):
    cur.execute('''UPDATE short SET interval_short=? WHERE tg_id=?''', (interval_short, tg_id))
    db.commit()


async def db_result_short(tg_id):
    result = cur.execute('''SELECT changes_short, interval_short FROM short WHERE tg_id=?''', (tg_id,)).fetchone()
    return result


async def user_id():
    result = cur.execute('''SELECT tg_id, date_of_start FROM users''').fetchall()
    return result


async def long_interval_user(interval_long, symbol):
    added_date = datetime.datetime.now() - datetime.timedelta(minutes=1)
    return cur.execute('''SELECT lastPrice FROM bybit WHERE symbol=? and date_lp>? ORDER BY date_lp DESC LIMIT 1''', (symbol, added_date)).fetchone()









