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
            ''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS quantity_user (
            tg_id INTEGER PRIMARY KEY,
            quantity_setting INTEGER,
            quantity_interval INTEGER)''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS long (
            tg_id INTEGER PRIMARY KEY,
            changes_long INTEGER,
            interval_long INTEGER)''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS short (
            tg_id INTEGER PRIMARY KEY,
            changes_short INTEGER,
            interval_short INTEGER)''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS bybit_symbol (symbol TEXT PRIMARY KEY)''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS bybit (
            symbol TEXT,
            lastPrice TEXT,
            openInterest TEXT,
            volume TEXT,
            date_lp TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS quantity_signal (
            tg_id INTEGER,
            symbol TEXT,
            date_sgnl TEXT
            )
            ''') as cursor: pass


async def db_bybit_smbl(symbol):
    async with aiosqlite.connect('database/database.db') as db:
        smbl = await db.execute('''SELECT 1 FROM bybit_symbol WHERE symbol=?''', (symbol,))
        smbl = await smbl.fetchone()
        if smbl is None:
            await db.execute('''INSERT INTO bybit_symbol(symbol) VALUES (?)''', (symbol,))
            await db.commit()


async def db_bybit(symbol, lp, oi, vlm):
    async with aiosqlite.connect('database/database.db') as db:
        count = await db.execute('''SELECT COUNT(*) FROM bybit WHERE symbol=?''', (symbol,))
        count = await count.fetchone()
        if count[0] > 4800:
            await db.execute('''DELETE FROM bybit WHERE symbol={key} ORDER BY ROWID LIMIT 1'''.format(key=symbol))
        await db.execute('''INSERT INTO bybit(
        symbol, lastPrice, openInterest, volume, date_lp) VALUES (
        ?, ?, ?, ?, datetime('now'))''', (
            symbol, lp, oi, vlm))
        await db.commit()


async def db_create_user(tg_id, username, first_name, last_name):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT 1 FROM users WHERE tg_id={key}'''.format(key=tg_id))
        result = await result.fetchone()
        if result is None:
            await db.execute('''INSERT INTO users (
            tg_id, username, first_name, last_name, date_of_start) 
            VALUES (
            ?, ?, ?, ?, datetime('now'))''', (
                tg_id, username, first_name, last_name)
                             )
            await db.execute('''INSERT INTO long (
            tg_id, changes_long, interval_long
            )
            VALUES (?, ?, ?)''', (
                tg_id, 10, 30)
                             )
            await db.execute('''INSERT INTO short (
            tg_id, changes_short, interval_short
            )
            VALUES (?, ?, ?)''', (
                tg_id, -10, 30)
                             )
            await db.execute('''INSERT INTO quantity_user 
            (tg_id, quantity_setting, quantity_interval) VALUES (?,?,?)''', (tg_id, 1, 30))
            await db.commit()


async def db_changes_long(tg_id, changes_long):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE long SET changes_long=? WHERE tg_id=?''', (changes_long, tg_id))
        await db.commit()


async def db_interval_long(tg_id, interval_long):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE long SET interval_long=? WHERE tg_id=?''', (interval_long, tg_id))
        await db.commit()


async def db_quantity_setting(tg_id, quantity_setting):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE quantity_user SET quantity_setting=? WHERE tg_id=?''', (quantity_setting, tg_id))
        await db.commit()


async def db_quantity_interval(tg_id, quantity_interval):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE quantity_user SET quantity_interval=? WHERE tg_id=?''', (quantity_interval, tg_id))
        await db.commit()


async def db_quantity_selection(tg_id):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT quantity_setting, quantity_interval FROM quantity_user WHERE tg_id=?''', (tg_id, ))
        result = await result.fetchone()
        return result


async def db_result_long(tg_id):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute(
            '''SELECT changes_long, interval_long FROM long WHERE tg_id={key}'''.format(key=tg_id))
        result = await result.fetchone()
        return result


async def db_changes_short(tg_id, changes_short):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE short SET changes_short=? WHERE tg_id=?''', (changes_short, tg_id))
        await db.commit()


async def db_interval_short(tg_id, interval_short):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE short SET interval_short=? WHERE tg_id=?''', (interval_short, tg_id))
        await db.commit()


async def db_result_short(tg_id):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT changes_short, interval_short FROM short WHERE tg_id=?''',
                                  (tg_id,))
        result = await result.fetchone()
        return result


async def user_id():
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT tg_id, date_of_start FROM users''')
        result = await result.fetchall()
        return result


async def long_interval_user(interval_long, symbol):
    async with aiosqlite.connect('database/database.db') as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT lastPrice FROM bybit WHERE symbol=? and 
        date_lp<? ORDER BY date_lp''', (symbol, added_date))
        result = await result.fetchall()
        return result


async def quantity(tg_id, symbol):
    async with aiosqlite.connect('database/database.db') as db:
        symbol_signal = await db.execute('''SELECT 1 FROM quantity_signal WHERE tg_id=? and symbol=?''', (tg_id, symbol))
        symbol_signal = await symbol_signal.fetchone()
        quantity_tg_ig = await db.execute('''SELECT quantity_setting, quantity_interval FROM 
                quantity_user WHERE tg_id = ?''', (tg_id,))
        quantity_tg_ig = await quantity_tg_ig.fetchone()
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=quantity_tg_ig[1])
        dt_base = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
        (tg_id=? and symbol=? and date_sgnl>?) ORDER BY date_sgnl''', (tg_id, symbol, dt))
        quantity_count = await quantity_count.fetchone()
        quantity_count_base = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
                (tg_id=? and symbol=? and date_sgnl>?) ORDER BY date_sgnl''', (tg_id, symbol, dt_base))
        quantity_count_base = await quantity_count_base.fetchone()
        if symbol_signal is None:
            await db.execute('''INSERT INTO quantity_signal (tg_id, symbol, date_sgnl) VALUES (
            ?, ?, datetime('now'))''', (tg_id, symbol))
            await db.commit()
            return True
        elif quantity_count[0] < quantity_tg_ig[0]:
            if quantity_count_base[0] < 1:
                await db.execute('''INSERT INTO quantity_signal (tg_id, symbol, date_sgnl) 
                VALUES (?, ?, datetime('now'))''', (tg_id, symbol))
                await db.commit()
                return True
        else:
            return False


async def clear_quantity_signal(tg_id, symbol):
    async with aiosqlite.connect('database/database.db') as db:
        dt_cl = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1440)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
                (tg_id=? and symbol=? and date_sgnl>?) ORDER BY date_sgnl''', (tg_id, symbol, dt_cl))
        quantity_count = await quantity_count.fetchone()
        await db.execute('''DELETE FROM quantity_signal WHERE (
        tg_id=? and symbol=? and date_sgnl<?)''',
                         (tg_id, symbol, dt_cl))
        await db.commit()
        return quantity_count[0]



