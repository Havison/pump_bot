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

        async with db.execute('''
            CREATE TABLE IF NOT EXISTS binance (
            symbol TEXT,
            lastPrice TEXT,
            openInterest TEXT,
            volume TEXT,
            date_lp TEXT
            )
            ''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS quantity_user (
            tg_id INTEGER PRIMARY KEY,
            quantity_setting INTEGER,
            quantity_interval INTEGER,
            quantity_setting_long INTEGER,
            quantity_interval_long INTEGER)''') as cursor: pass

        async with db.execute('''CREATE TABLE IF NOT EXISTS setting_signal (
            tg_id INTEGER PRIMARY KEY,
            changes_long INTEGER,
            interval_long INTEGER,
            changes_short INTEGER,
            interval_short INTEGER,
            binance INTEGER,
            bybit INTEGER,
            open_interes INTEGER,
            open_interes_interval INTEGER,
            changes_long_mini INTEGER,
            changes_mini_interval INTEGER,
            quantity_setting INTEGER,
            quantity_interval INTEGER)''') as cursor: pass

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
            date_sgnl TEXT,
            market TEXT,
            short INTEGER
            )
            ''') as cursor: pass

        async with db.execute('''
        CREATE TABLE IF NOT EXISTS stop_signal (
            tg_id INTEGER,
            state INTEGER
            )
            ''') as cursor: pass


async def db_bybit(symbol):
    async with aiosqlite.connect('database/database.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM bybit WHERE date_lp<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO bybit(
        symbol, lastPrice, openInterest, volume, date_lp) VALUES (
        ?, ?, ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def db_binance(symbol):
    async with aiosqlite.connect('database/database.db') as db:
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=240)
        await db.execute('''DELETE FROM binance WHERE date_lp<?''', (dt,))
        await db.commit()
        await db.executemany('''INSERT INTO binance(
        symbol, lastPrice, openInterest, volume, date_lp) VALUES (
        ?, ?, ?, ?, datetime('now'))''', symbol)
        await db.commit()


async def db_create_user(tg_id, username, first_name, last_name):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT 1 FROM users WHERE tg_id=?''', (tg_id,))
        result = await result.fetchone()
        if result is None:
            await db.execute('''INSERT INTO users (
            tg_id, username, first_name, last_name, date_of_start) 
            VALUES (
            ?, ?, ?, ?, datetime('now', '+3 days'))''', (
                tg_id, username, first_name, last_name)
                             )
            await db.commit()
            await db.execute('''INSERT INTO setting_signal (
            tg_id, changes_long, interval_long, 
            changes_short, interval_short, binance, 
            bybit, open_interes, open_interes_interval, 
            changes_long_mini, changes_mini_interval, 
            quantity_setting, quantity_interval
            )
            VALUES (?, 10, 30, -10, 30, 1, 1, 3, 20, 3, 3, 1, 30)''', (
                tg_id,)
                             )
            await db.commit()

            await db.execute('''INSERT INTO stop_signal (tg_id, state)
            VALUES (?, 1)''', (tg_id,))
            await db.commit()


async def db_changes_long(tg_id, changes_long):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET changes_long=? WHERE tg_id=?''', (changes_long, tg_id))
        await db.commit()


async def db_interval_long(tg_id, interval_long):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET interval_long=? WHERE tg_id=?''', (interval_long, tg_id))
        await db.commit()


async def db_quantity_setting(tg_id, quantity_setting):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET quantity_setting=? WHERE tg_id=?''', (quantity_setting, tg_id))
        await db.commit()


async def db_quantity_interval(tg_id, quantity_interval):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET quantity_interval=? WHERE tg_id=?''', (quantity_interval, tg_id))
        await db.commit()


async def db_changes_short(tg_id, changes_short):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET changes_short=? WHERE tg_id=?''', (changes_short, tg_id))
        await db.commit()


async def db_interval_short(tg_id, interval_short):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE setting_signal SET interval_short=? WHERE tg_id=?''', (interval_short, tg_id))
        await db.commit()


async def db_setting_selection(tg_id):
    async with aiosqlite.connect('database/database.db') as db:
        result = await db.execute('''SELECT changes_long, interval_long, 
            changes_short, interval_short, binance, 
            bybit, open_interes, open_interes_interval, 
            changes_long_mini, changes_mini_interval, 
            quantity_setting, quantity_interval 
            FROM setting_signal WHERE tg_id=?''', (tg_id,))
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
        date_lp>? ORDER BY date_lp''', (symbol, added_date))
        result = await result.fetchall()
        return result


async def long_interval_user_binance(interval_long, symbol):
    async with aiosqlite.connect('database/database.db') as db:
        added_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_long)
        result = await db.execute('''SELECT lastPrice FROM binance WHERE symbol=? and 
        date_lp>? ORDER BY date_lp''', (symbol, added_date))
        result = await result.fetchall()
        return result


async def market_setting(tg_id, market, on_off):
    async with aiosqlite.connect('database/database.db') as db:
        if market == 'bybit':
            await db.execute('''UPDATE setting_signal SET bybit=? WHERE (tg_id=?)''', (on_off, tg_id))
            await db.commit()
        elif market == 'binance':
            await db.execute('''UPDATE setting_signal SET binance=? WHERE (tg_id=?)''', (on_off, tg_id))
            await db.commit()


async def quantity(tg_id, symbol, interval_user, market, short):
    async with aiosqlite.connect('database/database.db') as db:
        symbol_signal = await db.execute('''SELECT 1 FROM quantity_signal WHERE 
        tg_id=? and symbol=? and market=? and short=?''', (tg_id, symbol, market, short))
        symbol_signal = await symbol_signal.fetchone()
        quantity_tg_ig = await db.execute('''SELECT quantity_setting, quantity_interval FROM 
                setting_signal WHERE tg_id = ?''', (tg_id,))
        quantity_tg_ig = await quantity_tg_ig.fetchone()
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=quantity_tg_ig[1])
        dt_base = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=interval_user + 1)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
        (tg_id=? and symbol=? and date_sgnl>? and market=? and short=?) ORDER BY date_sgnl''',
                                          (tg_id, symbol, dt, market, short))
        quantity_count = await quantity_count.fetchone()
        quantity_count_base = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
                (tg_id=? and symbol=? and date_sgnl>? and market=? and short=?) ORDER BY date_sgnl''',
                                               (tg_id, symbol, dt_base, market, short))
        quantity_count_base = await quantity_count_base.fetchone()
        if symbol_signal is None:
            await db.execute('''INSERT INTO quantity_signal (tg_id, symbol, date_sgnl, market, short) VALUES (
            ?, ?, datetime('now'), ?, ?)''', (tg_id, symbol, market, short))
            await db.commit()
            return True
        elif quantity_count[0] < quantity_tg_ig[0]:
            if quantity_count_base[0] < 1:
                await db.execute('''INSERT INTO quantity_signal (tg_id, symbol, date_sgnl, market, short) 
                VALUES (?, ?, datetime('now'), ?, ?)''', (tg_id, symbol, market, short))
                await db.commit()
                return True
        else:
            return False


async def clear_quantity_signal(tg_id, symbol, market, short):
    async with aiosqlite.connect('database/database.db') as db:
        dt_cl = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1440)
        quantity_count = await db.execute('''SELECT COUNT(*) FROM quantity_signal WHERE 
                (tg_id=? and symbol=? and date_sgnl>? and market=? and short=?) ORDER BY date_sgnl''',
                                          (tg_id, symbol, dt_cl, market, short))
        quantity_count = await quantity_count.fetchone()
        await db.execute('''DELETE FROM quantity_signal WHERE (
        tg_id=? and symbol=? and date_sgnl<? and market=? and short=?)''',
                         (tg_id, symbol, dt_cl, market, short))
        await db.commit()
        return quantity_count[0]


async def premium_user(tg_id):  #функция проверяет на подписку
    async with aiosqlite.connect('database/database.db') as db:
        today = datetime.datetime.now(datetime.timezone.utc)
        premium = await db.execute('''SELECT date_of_start FROM users WHERE (tg_id=? and date_of_start>?)''',
                                   (tg_id, today))
        premium = await premium.fetchone()
        if premium is None:
            return False
        else:
            return premium


async def premium_setting(tg_id, days):
    if days == '1':
        async with aiosqlite.connect('database/database.db') as db:
            await db.execute('''UPDATE users SET date_of_start=datetime(datetime('now'), '+1 days') WHERE (tg_id=?)''',
                             (tg_id,))
            await db.commit()
    if days == '10':
        async with aiosqlite.connect('database/database.db') as db:
            await db.execute('''UPDATE users SET date_of_start=datetime(datetime('now'), '+10 days') WHERE (tg_id=?)''',
                             (tg_id,))
            await db.commit()
    if days == '30':
        async with aiosqlite.connect('database/database.db') as db:
            await db.execute('''UPDATE users SET date_of_start=datetime(datetime('now'), '+30 days') WHERE (tg_id=?)''',
                             (tg_id,))
            await db.commit()


async def stop_signal(tg_id, state):
    async with aiosqlite.connect('database/database.db') as db:
        await db.execute('''UPDATE stop_signal SET state=? WHERE (tg_id=?)''', (state, tg_id))
        await db.commit()

async def state_signal(tg_id):
    async with aiosqlite.connect('database/database.db') as db:
        state_signal_user = await db.execute('''SELECT state FROM stop_signal WHERE (tg_id=?)''',
                                   (tg_id, ))
        state_signal_user = await state_signal_user.fetchone()
        return state_signal_user



