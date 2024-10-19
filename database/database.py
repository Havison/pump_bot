import datetime
import aiosqlite


async def db_start():
    async with aiosqlite.connect('database/database.db') as db:
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
            symbol TEXT,
            date_signal TEXT,
            short INTEGER
            )
            ''') as cursor: pass


async def db_start_binance():
    async with aiosqlite.connect('database/database_binance.db') as db:
        async with db.execute('''
            CREATE TABLE IF NOT EXISTS binance (
            symbol TEXT,
            last_prise TEXT,
            date_create TEXT
            )
            ''') as cursor: pass

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS quantity_user_signal (
            symbol TEXT,
            date_signal TEXT,
            short INTEGER
            )
            ''') as cursor: pass


async def db_bybit(symbol):
    async with aiosqlite.connect('database/database.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM bybit WHERE date_create<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO bybit(
        symbol, last_prise, oi, date_create) VALUES (
        ?, ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def db_binance(symbol):
    async with aiosqlite.connect('database/database_binance.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM binance WHERE date_create<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO binance(
        symbol, last_prise, date_create) VALUES (
        ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def long_interval_user(interval_long, symbol):
    async with aiosqlite.connect('database/database.db') as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT last_prise FROM 
        bybit WHERE date_create>? and symbol=? ORDER BY date_create''', (added_date, symbol))
        result = await result.fetchall()
        return result


async def long_interval_user_binance(interval_long, symbol):
    async with aiosqlite.connect('database/database_binance.db') as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT last_prise FROM 
        binance WHERE date_create>? and symbol=? ORDER BY date_create''', (added_date, symbol))
        result = await result.fetchall()
        return result


async def quantity(symbol, interval, short):
    async with aiosqlite.connect('database/database.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval + 1)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE (symbol=? and date_signal>? and short=?) ORDER BY date_signal''', (symbol, dt, short))
        quantity_count = await quantity_count.fetchone()
        dt = datetime.datetime.now(datetime.timezone.utc)
        if quantity_count[0] < 1:
            await db.execute('''INSERT INTO quantity_user_signal (symbol, date_signal, short)
            VALUES (?, ?, ?)''', (symbol, dt, short))
            await db.commit()
            return True
        else:
            return False


async def clear_quantity_signal(symbol, interval, short):
    async with aiosqlite.connect('database/database.db') as db:
        dt_delete = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1441)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (symbol=? and date_signal>? and short=?) ORDER BY date_signal''',
                                          (symbol, dt_delete, short))
        quantity_count = await quantity_count.fetchone()
        await db.execute('''DELETE FROM quantity_user_signal WHERE (symbol=? and date_signal<? and short=?)''',
                         (symbol, dt_delete, short))
        await db.commit()
        return quantity_count[0]


async def quantity_binance(symbol, interval, short):
    async with aiosqlite.connect('database/database_binance.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval + 1)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE (symbol=? and date_signal>? and short=?) ORDER BY date_signal''',
                                          (symbol, dt, short))
        quantity_count = await quantity_count.fetchone()
        dt = datetime.datetime.now(datetime.timezone.utc)
        if quantity_count[0] < 1:
            await db.execute('''INSERT INTO quantity_user_signal (symbol, date_signal, short)
            VALUES (?, ?, ?)''', (symbol, dt, short))
            await db.commit()
            return True
        else:
            return False


async def clear_quantity_signal_binance(symbol, interval, short):
    async with aiosqlite.connect('database/database_binance.db') as db:
        dt_delete = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1441)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_user_signal WHERE
                (symbol=? and date_signal>? and short=?) ORDER BY date_signal''',
                                          (symbol, dt_delete, short))
        quantity_count = await quantity_count.fetchone()
        await db.execute('''DELETE FROM quantity_user_signal WHERE (symbol=? and date_signal<? and short=?)''',
                         (symbol, dt_delete, short))
        await db.commit()
        return quantity_count[0]


