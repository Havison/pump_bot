from aiogram import F, Router, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from lexicon.lexicon import LEXICON, LEXICON_TEXT
import database as db
import humanize
from config_data.config import Config, load_config

config: Config = load_config('.env')
bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

_i = humanize.i18n.activate('ru_RU')
storage = MemoryStorage()
router = Router()


class FSMLongSort(StatesGroup):
    changes_long = State()  #состояние ожидание ввода роста в процентах
    interval_long = State()  #состояние ожидание ввода интервала роста в минутах
    changes_short = State()  #состояние ожидание ввода падения в процентах
    interval_short = State()  #состояние ожидание ввода интервала падения в минутах
    quantity_setting = State()
    quantity_interval = State()
    admin = State()
    market = State()


# Создаем объекты кнопок
button_1 = KeyboardButton(text=LEXICON['/setting'])
button_2 = KeyboardButton(text=LEXICON['/profile'])
button_3 = KeyboardButton(text=LEXICON['/help'])
button_4 = KeyboardButton(text=LEXICON['/pump'])
button_5 = KeyboardButton(text=LEXICON['/dump'])
button_6 = KeyboardButton(text=LEXICON['/quantity'])
button_7 = KeyboardButton(text=LEXICON['/bybit'])
button_8 = KeyboardButton(text=LEXICON['/chanel'])
button_9 = KeyboardButton(text=LEXICON['/hours_24'])
button_10 = KeyboardButton(text=LEXICON['/hours_12'])
button_11 = KeyboardButton(text=LEXICON['/hours_6'])
button_12 = KeyboardButton(text=LEXICON['/on_limited'])
button_13 = KeyboardButton(text=LEXICON['/binance'])
button_14 = KeyboardButton(text=LEXICON['/market'])
button_15 = KeyboardButton(text=LEXICON['/bybit_off'])
button_16 = KeyboardButton(text=LEXICON['/binance_off'])

# Создаем объект клавиатуры, добавляя в него кнопки
keyboard_button = ReplyKeyboardMarkup(keyboard=[[button_1, button_2, button_3]], resize_keyboard=True)
keyboard_button_setting = ReplyKeyboardMarkup(keyboard=[[button_4, button_5, button_6], [button_14, button_8]],
                                              resize_keyboard=True)
keyboard_button_chanel = ReplyKeyboardMarkup(keyboard=[[button_8]], resize_keyboard=True)
keyboard_button_quantity = ReplyKeyboardMarkup(keyboard=[[button_9, button_10], [button_11, button_12], [button_8]],
                                               resize_keyboard=True)


async def setting_status(tg_id, message: Message):
    setting_user = await db.db_setting_selection(tg_id)
    hours_text = {30: 'часа', 360: 'часов', 720: 'часов', 1440: 'часа'}
    quantity_text = '<b>🧿Количество сигналов без ограничений🧿</b>'
    quantity_text_limit = (
        '🧿<b>Количество сигналов за {quantity_interval} '
        '{hours_text}: {quantity_setting}</b>🧿'
    ).format(quantity_interval=int(setting_user[11]/60),
             hours_text=hours_text[setting_user[11]],
             quantity_setting=setting_user[10])
    if setting_user[11] == 30:
        return LEXICON_TEXT['setting_text'].format(
            changes_long=setting_user[0], interval_long=setting_user[1],
            changes_short=setting_user[2], interval_short=setting_user[3],
            quantity_text=quantity_text)
    else:
        return LEXICON_TEXT['setting_text'].format(
            changes_long=setting_user[0], interval_long=setting_user[1],
            changes_short=setting_user[2], interval_short=setting_user[3],
            quantity_text=quantity_text_limit)


@router.message(CommandStart(), StateFilter(default_state))  # Этот хэндлер срабатывает на команду /start
async def process_start_command(message: Message):
    await db.db_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                            message.from_user.last_name)
    await message.answer(text=LEXICON['/start'],
                         reply_markup=keyboard_button)


@router.message(F.text == LEXICON['/chanel'])
async def process_chanel_press(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=LEXICON_TEXT['chanel'], reply_markup=keyboard_button)


@router.message(Command(commands='help'), StateFilter(default_state))
@router.message(F.text == LEXICON['/help'], StateFilter(default_state))# Этот хэндлер срабатывает на команду /help
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_TEXT['help'])


@router.message(Command(commands='reset'), StateFilter(default_state))
async def process_reset_command(message: Message):
    prm_date = await db.premium_user(message.from_user.id)
    if not prm_date:
        await message.answer(text=LEXICON_TEXT['fail_premium'])
    else:
        await db.db_changes_long(message.from_user.id, 10)
        await db.db_changes_short(message.from_user.id, -10)
        await db.db_interval_long(message.from_user.id, 30)
        await db.db_interval_short(message.from_user.id, 30)
        await db.db_quantity_interval(message.from_user.id, 30)
        await db.db_quantity_setting(message.from_user.id, 1)
        t = await setting_status(message.from_user.id, message)
        await message.answer(text=t)


@router.message(F.text == LEXICON['/setting'], StateFilter(default_state))
@router.message(Command(commands='setting'),
                StateFilter(default_state))  # Этот хэндлер срабатывает на команду /setting
async def process_settings_command(message: Message):
    prm_date = await db.premium_user(message.from_user.id)
    if not prm_date:
        await message.answer(text=LEXICON_TEXT['fail_premium'])
    else:
        t = await setting_status(message.from_user.id, message)
        await message.answer(text=t, reply_markup=keyboard_button_setting)

@router.message(F.text == LEXICON['/pump'], StateFilter(default_state))
async def process_long_press(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON_TEXT['long_setting_changes'], reply_markup=keyboard_button_chanel)
    #устаналиваем состояние вводе роста
    await state.set_state(FSMLongSort.changes_long)


@router.message(StateFilter(FSMLongSort.changes_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def long_setting_changes(message: Message, state: FSMContext):
    await db.db_changes_long(message.from_user.id, int(message.text))
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_long)


@router.message(StateFilter(FSMLongSort.interval_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 240)
async def long_setting_interval(message: Message, state: FSMContext):
    await db.db_interval_long(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id, message)
    await message.answer(text=t, reply_markup=keyboard_button)
    await state.clear()


@router.message(StateFilter(FSMLongSort.changes_long))
async def warning_long_changes(message: Message):
    await message.answer(text=LEXICON_TEXT['warning_long_changes'], reply_markup=keyboard_button_chanel)


@router.message(F.text == LEXICON['/dump'], StateFilter(default_state))
async def process_short_press(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON_TEXT['short_setting_changes'], reply_markup=keyboard_button_chanel)
    #устаналиваем состояние вводе роста
    await state.set_state(FSMLongSort.changes_short)


@router.message(StateFilter(FSMLongSort.changes_short),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def short_setting_changes(message: Message, state: FSMContext):
    await db.db_changes_short(message.from_user.id, int('-' + message.text))
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_short)


@router.message(StateFilter(FSMLongSort.interval_short),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 240)
async def long_setting_interval(message: Message, state: FSMContext):
    await db.db_interval_short(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id, message)
    await message.answer(text=t, reply_markup=keyboard_button)
    await state.clear()


@router.message(StateFilter(FSMLongSort.changes_short))
async def warning_long_changes(message: Message):
    await message.answer(text=LEXICON_TEXT['warning_short_changes'], reply_markup=keyboard_button_chanel)


@router.message(StateFilter(FSMLongSort.interval_long))
@router.message(StateFilter(FSMLongSort.interval_short))
async def warning_interval(message: Message):
    await message.answer(text=LEXICON_TEXT['warning_interval'], reply_markup=keyboard_button_chanel)


@router.message(F.text == LEXICON['/quantity'], StateFilter(default_state))
async def process_short_press(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON_TEXT['quantity_interval'], reply_markup=keyboard_button_quantity)
    #устаналиваем состояние вводе роста
    await state.set_state(FSMLongSort.quantity_interval)


@router.message(F.text == LEXICON['/hours_24'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/hours_12'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/hours_6'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/on_limited'], StateFilter(FSMLongSort.quantity_interval))
async def quantity_interval_setting(message: Message, state: FSMContext):
    if message.text == LEXICON['/on_limited']:
        qi = 30
        await db.db_quantity_interval(message.from_user.id, qi)
        t = await setting_status(message.from_user.id, message)
        await message.answer(text=t, reply_markup=keyboard_button)
        await db.db_quantity_setting(message.from_user.id, 1)
        await state.clear()
    if message.text == LEXICON['/hours_24']:
        qi = 24 * 60
        await db.db_quantity_interval(message.from_user.id, qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLongSort.quantity_setting)
    if message.text == LEXICON['/hours_12']:
        qi = 12 * 60
        await db.db_quantity_interval(message.from_user.id, qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLongSort.quantity_setting)
    if message.text == LEXICON['/hours_6']:
        qi = 6 * 60
        await db.db_quantity_interval(message.from_user.id, qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLongSort.quantity_setting)


@router.message(StateFilter(FSMLongSort.quantity_setting),
                lambda x: x.text.isdigit() and 1 <= int(x.text))
async def quantity_setting(message: Message, state: FSMContext):
    await db.db_quantity_setting(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id, message)
    await message.answer(text=t, reply_markup=keyboard_button)
    await state.clear()


@router.message(StateFilter(FSMLongSort.quantity_interval))
@router.message(StateFilter(FSMLongSort.quantity_setting))
async def quantity_warning(message: Message):
    await message.answer(text=LEXICON_TEXT['quantity_warning'])


@router.message(F.text == LEXICON['/profile'], StateFilter(default_state))
@router.message(Command(commands='profile'), StateFilter(default_state))
async def time_premium(message: Message):
    prm_date = await db.premium_user(message.from_user.id)
    if not prm_date:
        await message.answer(text=LEXICON_TEXT['fail_premium'])
    else:
        await message.answer(text=LEXICON_TEXT['premium'].format(prm_date=prm_date[0]))

async def message_long(tg_id, lp, symbol, interval, q, qi='За 24 часа'):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    bybit = f'https://www.bybit.com/trade/usdt/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'🟢<b>{symbol[0:-4]}</b>\n'
                                               f'<b>⚫ByBit</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Количество сигналов {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{bybit}\">ByBit</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


@router.message(F.text == LEXICON['/market'], StateFilter(default_state))
async def press_market(message: Message, state):
    market = await db.db_setting_selection(message.from_user.id)
    binance = market[4]
    bybit = market[5]
    print(market)
    print(binance, bybit)
    if binance and bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_7, button_13], [button_8]],
            resize_keyboard=True))
        await state.set_state(FSMLongSort.market)
    elif binance and not bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_15, button_13], [button_8]],
            resize_keyboard=True))
        await state.set_state(FSMLongSort.market)
    elif not binance and bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_7, button_16], [button_8]],
            resize_keyboard=True))
        await state.set_state(FSMLongSort.market)
    else:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_15, button_16], [button_8]],
            resize_keyboard=True))
        await state.set_state(FSMLongSort.market)


@router.message(F.text == LEXICON['/bybit'], StateFilter(FSMLongSort.market))
@router.message(F.text == LEXICON['/bybit_off'], StateFilter(FSMLongSort.market))
async def bybit_off(message: Message, state: FSMContext):
    market = await db.db_setting_selection(message.from_user.id)
    bybit = market[5]
    if bybit:
        await db.market_setting(message.from_user.id, 'bybit', 0)
        await state.clear()
        await press_market(message, state)
    else:
        await db.market_setting(message.from_user.id, 'bybit', 1)
        await state.clear()
        await press_market(message, state)


@router.message(F.text == LEXICON['/binance'], StateFilter(FSMLongSort.market))
@router.message(F.text == LEXICON['/binance_off'], StateFilter(FSMLongSort.market))
async def bybit_off(message: Message, state: FSMContext):
    market = await db.db_setting_selection(message.from_user.id)
    binance = market[4]
    if binance:
        await db.market_setting(message.from_user.id, 'binance', 0)
        await state.clear()
        await press_market(message, state)
    else:
        await db.market_setting(message.from_user.id, 'binance', 1)
        await state.clear()
        await press_market(message, state)






async def message_short(tg_id, lp, symbol, interval, q, qi='За 24 часа'):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    bybit = f'https://www.bybit.com/trade/usdt/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'🔴<b>{symbol[0:-4]}</b>\n'
                                               f'<b>⚫ByBit</b>\n'
                                               f'Изменения за {interval} минут\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Количество сигналов за {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{bybit}\">ByBit</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


async def message_long_binance(tg_id, lp, symbol, interval, q, qi='За 24 часа'):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    binance = f'https://www.binance.com/ru/futures/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'🟢<b>{symbol[0:-4]}</b>\n'
                                               f'<b>🟡Binance</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Количество сигналов {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{binance}\">Binance</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


async def message_short_binance(tg_id, lp, symbol, interval, q, qi='За 24 часа'):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    binance = f'https://www.binance.com/ru/futures/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'🔴<b>{symbol[0:-4]}</b>\n'
                                               f'<b>🌕Binance</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Количество сигналов за {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{binance}\">Binance</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


@router.message(Command(commands='713452603Havi'), StateFilter(default_state))
async def prem_id(message: Message, state: FSMContext):
    if message.from_user.id == 573167949:
        await state.set_state(FSMLongSort.admin)
    else:
        return


@router.message(StateFilter(FSMLongSort.admin))
async def prem(message: Message, state: FSMContext):
    id_tg = message.text.split(' ')
    await db.premium_setting(id_tg[0], id_tg[1])
    await state.clear()

