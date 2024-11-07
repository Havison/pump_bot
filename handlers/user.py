from aiogram import F, Router, Bot
import logging
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from lexicon.lexicon import LEXICON, LEXICON_TEXT
import database as db
import humanize
from config_data.config import Config, load_config
from cloud_pay.paymant import CryptoCloudSDK

config: Config = load_config('.env')
bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

create_invoice = CryptoCloudSDK()


logger3 = logging.getLogger(__name__)
handler3 = logging.FileHandler(f"{__name__}.log")
formatter3 = logging.Formatter("%(filename)s:%(lineno)d #%(levelname)-8s "
                               "[%(asctime)s] - %(name)s - %(message)s")
handler3.setFormatter(formatter3)
logger3.addHandler(handler3)
logger3.info(f"Testing the custom logger for module {__name__}")

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
    quantity_interval_min = State()
    quantity_setting_min = State()
    changes_long_min = State()
    interval_long_min = State()
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
button_17 = KeyboardButton(text=LEXICON['/prem'])
button_18 = KeyboardButton(text=LEXICON['/long'])
button_19 = KeyboardButton(text=LEXICON['/quantity_pd'])
button_20 = KeyboardButton(text=LEXICON['/quantity_pm'])


# Создаем объект клавиатуры, добавляя в него кнопки
keyboard_button = ReplyKeyboardMarkup(keyboard=[[button_1 ,button_3, button_17]], resize_keyboard=True)
keyboard_button_setting = ReplyKeyboardMarkup(keyboard=[[button_4, button_5, button_18], [button_6, button_14, button_8]],
                                              resize_keyboard=True)
keyboard_button_chanel = ReplyKeyboardMarkup(keyboard=[[button_8]], resize_keyboard=True)
keyboard_button_quantity = ReplyKeyboardMarkup(keyboard=[[button_9, button_10], [button_11, button_12], [button_8]],
                                               resize_keyboard=True)


async def not_prem(message: Message):
    result = await db.premium_user(message.from_user.id)
    if result:
        return True
    else:
        await message.answer(text=LEXICON_TEXT['not_prem'])
        await process_prem(message)
        return False


async def setting_status(tg_id):
    setting_user = await db.db_setting_selection(tg_id)
    hours_text = {3: 'часа', 30: 'часа', 360: 'часов', 720: 'часов', 1440: 'часа'}
    quantity_text = '<b>🧿Кол-во сигналов не ограничено🧿</b>'
    quantity_text_limit = '🧿<b>Кол-во сигналов за {quantity_interval} {hours_text}: {quantity_setting}</b>🧿'
    if setting_user['interval_signal_pd'] == 30:
        q_text = quantity_text
    else:
        q_text = quantity_text_limit.format(
            quantity_interval=int(setting_user['interval_signal_pd']/60),
            hours_text=hours_text[setting_user['interval_signal_pd']],
            quantity_setting=setting_user['quantity_signal_pd'])
    if setting_user['interval_signal_pm'] == 3:
        q_text_min = quantity_text
    else:
        q_text_min = quantity_text_limit.format(
            quantity_interval=int(setting_user['interval_signal_pm']/60),
            hours_text=hours_text[setting_user['interval_signal_pm']],
            quantity_setting=setting_user['quantity_signal_pm'])
    return LEXICON_TEXT['setting_text'].format(
        changes_long=setting_user['quantity_pump'], interval_long=setting_user['interval_pump'],
        changes_short=setting_user['quantity_short'], interval_short=setting_user['interval_short'],
        changes_long_min=setting_user['quantity_pump_min'],
        intarval_long_min=setting_user['interval_pump_min'],
        quantity_text=q_text, quantity_text_min=q_text_min)


@router.message(CommandStart())  # Этот хэндлер срабатывает на команду /start
async def process_start_command(message: Message, state: FSMContext):
    await db.db_create_user(message.from_user.id, message.from_user.username)
    await message.answer(text=LEXICON['/start'],
                         reply_markup=keyboard_button)
    await state.clear()
    await db.stop_signal(message.from_user.id, 1)


@router.message(Command(commands='pay'))
@router.message(F.text == LEXICON['/prem'], StateFilter(default_state))
async def process_prem(message: Message):
    prm_date = await db.premium_user(message.from_user.id)
    if prm_date:
        await message.answer(text=LEXICON_TEXT['premium_pay'].format(prm_date=prm_date))
    else:
        data = {
            "amount": 10, "shop_id": 'yUwIRDANiwodkJ1f', "currency": 'USD', "order_id": message.from_user.id,
            "add_fields": {
                "time_to_pay": {
                    "hours": 0, "minutes": 30
                }
            }
        }
        ordder = create_invoice.create_invoice(data)
        t = ordder['result']['link']
        chanel = 'https://t.me/pump_dump_oi'
        button_inlaite_1 = InlineKeyboardButton(text=LEXICON['pay'], url=t)
        button_inlaite_2 = InlineKeyboardButton(text=LEXICON['free_play'], callback_data=LEXICON['free_play'])
        button_inlaite_3 = InlineKeyboardButton(text=LEXICON['chanel'], url=chanel)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_inlaite_1], [button_inlaite_2], [button_inlaite_3]])
        await message.answer(
            text=LEXICON_TEXT['pay_30'],
            reply_markup=keyboard
        )


@router.callback_query(F.data == LEXICON['free_play'], StateFilter(default_state))
async def process_free_play(callback: CallbackQuery):
    free_prem = await db.free_premium_user(callback.from_user.id)
    if free_prem:
        await callback.message.answer(text=LEXICON_TEXT['free_play'])
    else:
        await callback.message.answer(text=LEXICON_TEXT['free_play_on'])


@router.message(F.text == LEXICON['/chanel'])
async def process_chanel_press(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=LEXICON_TEXT['chanel'], reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)


@router.message(Command(commands='help'))
@router.message(F.text == LEXICON['/help'], StateFilter(default_state))# Этот хэндлер срабатывает на команду /help
async def process_help_command(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_TEXT['help'], reply_markup=keyboard_button)
    await state.clear()
    await db.stop_signal(message.from_user.id, 1)


@router.message(Command(commands='reset'))
async def process_reset_command(message: Message, state: FSMContext):
    premium = await not_prem(message)
    if not premium:
        return
    else:
        await db.db_changes_long(message.from_user.id, 10)
        await db.db_changes_short(message.from_user.id, -10)
        await db.db_interval_long(message.from_user.id, 30)
        await db.db_interval_short(message.from_user.id, 30)
        await db.db_quantity_interval(message.from_user.id, 30)
        await db.db_quantity_setting(message.from_user.id, 1)
        await db.db_changes_long_min(message.from_user.id, 3)
        await db.db_interval_long_min(message.from_user.id, 3)
        t = await setting_status(message.from_user.id)
        await message.answer(text=t, reply_markup=keyboard_button)
    await state.clear()
    await db.stop_signal(message.from_user.id, 1)


@router.message(Command(commands='profile'))
@router.message(F.text == LEXICON['/profile'], StateFilter(default_state))
async def time_premium(message: Message, state: FSMContext):
    premium = await not_prem(message)
    if not premium:
        return
    else:
        await message.answer(text=LEXICON_TEXT['premium'].format(prm_date=prm_date), reply_markup=keyboard_button)
    await state.clear()
    await db.stop_signal(message.from_user.id, 1)


@router.message(Command(commands='setting'))
@router.message(F.text == LEXICON['/setting'], StateFilter(default_state))  # Этот хэндлер срабатывает на команду /setting
async def process_settings_command(message: Message, state: FSMContext):
    premium = await not_prem(message)
    if not premium:
        return
    else:
        t = await setting_status(message.from_user.id)
        await message.answer(text=t, reply_markup=keyboard_button_setting)
    await state.clear()
    await db.stop_signal(message.from_user.id, 1)


@router.message(F.text == LEXICON['/pump'], StateFilter(default_state))
async def process_long_press(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON_TEXT['long_setting_changes'], reply_markup=keyboard_button_chanel)
    #устаналиваем состояние вводе роста
    await db.stop_signal(message.from_user.id, 0)
    await state.set_state(FSMLongSort.changes_long)


@router.message(StateFilter(FSMLongSort.changes_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def long_setting_changes(message: Message, state: FSMContext):
    changes_long = int(message.text)
    await state.update_data(changes_long=changes_long)
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_long)


@router.message(StateFilter(FSMLongSort.interval_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 120)
async def long_setting_interval(message: Message, state: FSMContext):
    data = await state.get_data()
    changes_long = data['changes_long']
    await db.db_changes_long(message.from_user.id, changes_long)
    await db.db_interval_long(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id)
    await message.answer(text=t, reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)
    await state.clear()


@router.message(F.text == LEXICON['/long'], StateFilter(default_state))
async def process_long_min_press(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_TEXT['long_setting_changes'], reply_markup=keyboard_button_chanel)
    await db.stop_signal(message.from_user.id, 0)
    await state.set_state(FSMLongSort.changes_long_min)


@router.message(StateFilter(FSMLongSort.changes_long_min),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def long_setting_changes(message: Message, state: FSMContext):
    changes_long_min = int(message.text)
    await state.update_data(changes_long_min=changes_long_min)
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_long_min)


@router.message(StateFilter(FSMLongSort.interval_long_min),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 120)
async def long_setting_interval(message: Message, state: FSMContext):
    data = await state.get_data()
    changes_long_min = data['changes_long_min']
    await db.db_changes_long_min(message.from_user.id, changes_long_min)
    await db.db_interval_long_min(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id)
    await message.answer(text=t, reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)
    await state.clear()


@router.message(StateFilter(FSMLongSort.changes_long_min))
@router.message(StateFilter(FSMLongSort.changes_long))
async def warning_long_changes(message: Message):
    await message.answer(text=LEXICON_TEXT['warning_long_changes'], reply_markup=keyboard_button_chanel)


@router.message(F.text == LEXICON['/dump'], StateFilter(default_state))
async def process_short_press(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON_TEXT['short_setting_changes'], reply_markup=keyboard_button_chanel)
    await db.stop_signal(message.from_user.id, 0)
    await state.set_state(FSMLongSort.changes_short)


@router.message(StateFilter(FSMLongSort.changes_short),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def short_setting_changes(message: Message, state: FSMContext):
    changes_short = int('-' + message.text)
    await state.update_data(changes_short=changes_short)
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_short)


@router.message(StateFilter(FSMLongSort.interval_short),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 240)
async def long_setting_interval(message: Message, state: FSMContext):
    data = await state.get_data()
    changes_short = data['changes_short']
    await db.db_changes_short(message.from_user.id, changes_short)
    await db.db_interval_short(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id)
    await message.answer(text=t, reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)
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
        text=LEXICON_TEXT['qunatity_pd_pm'],
        reply_markup=ReplyKeyboardMarkup(keyboard=[[button_19], [button_20], [button_8]],
                                         resize_keyboard=True))


@router.message(F.text == LEXICON['/quantity_pd'], StateFilter(default_state))
async def process_quantity_pd(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_TEXT['quantity_interval'], reply_markup=keyboard_button_quantity)
    await state.set_state(FSMLongSort.quantity_interval)


@router.message(F.text == LEXICON['/hours_24'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/hours_12'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/hours_6'], StateFilter(FSMLongSort.quantity_interval))
@router.message(F.text == LEXICON['/on_limited'], StateFilter(FSMLongSort.quantity_interval))
async def quantity_interval_setting(message: Message, state: FSMContext):
    await db.stop_signal(message.from_user.id, 0)
    if message.text == LEXICON['/on_limited']:
        qi = 30
        await db.db_quantity_interval(message.from_user.id, qi)
        t = await setting_status(message.from_user.id)
        await message.answer(text=t, reply_markup=keyboard_button)
        await db.db_quantity_setting(message.from_user.id, 1)
        await db.stop_signal(message.from_user.id, 1)
        await state.clear()
    if message.text == LEXICON['/hours_24']:
        qi = 24 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting)
    if message.text == LEXICON['/hours_12']:
        qi = 12 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting)
    if message.text == LEXICON['/hours_6']:
        qi = 6 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting)


@router.message(F.text == LEXICON['/quantity_pm'], StateFilter(default_state))
async def process_quantity_pm(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_TEXT['quantity_interval'], reply_markup=keyboard_button_quantity)
    await state.set_state(FSMLongSort.quantity_interval_min)


@router.message(F.text == LEXICON['/hours_24'], StateFilter(FSMLongSort.quantity_interval_min))
@router.message(F.text == LEXICON['/hours_12'], StateFilter(FSMLongSort.quantity_interval_min))
@router.message(F.text == LEXICON['/hours_6'], StateFilter(FSMLongSort.quantity_interval_min))
@router.message(F.text == LEXICON['/on_limited'], StateFilter(FSMLongSort.quantity_interval_min))
async def quantity_interval_setting_min(message: Message, state: FSMContext):
    await db.stop_signal(message.from_user.id, 0)
    if message.text == LEXICON['/on_limited']:
        qi = 3
        await db.db_quantity_interval_min(message.from_user.id, qi)
        t = await setting_status(message.from_user.id)
        await message.answer(text=t, reply_markup=keyboard_button)
        await db.db_quantity_setting_min(message.from_user.id, 1)
        await db.stop_signal(message.from_user.id, 1)
        await state.clear()
    if message.text == LEXICON['/hours_24']:
        qi = 24 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting_min)
    if message.text == LEXICON['/hours_12']:
        qi = 12 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting_min)
    if message.text == LEXICON['/hours_6']:
        qi = 6 * 60
        await state.update_data(qi=qi)
        await message.answer(text=LEXICON_TEXT['quantity_setting'], reply_markup=keyboard_button_chanel)
        await state.set_state(FSMLongSort.quantity_setting_min)


@router.message(StateFilter(FSMLongSort.quantity_setting),
                lambda x: x.text.isdigit() and 1 <= int(x.text))
async def quantity_setting(message: Message, state: FSMContext):
    data = await state.get_data()
    qi = data['qi']
    await db.db_quantity_interval(message.from_user.id, qi)
    await db.db_quantity_setting(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id)
    await message.answer(text=t, reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)
    await state.clear()


@router.message(StateFilter(FSMLongSort.quantity_setting_min),
                lambda x: x.text.isdigit() and 1 <= int(x.text))
async def quantity_setting_min(message: Message, state: FSMContext):
    data = await state.get_data()
    qi = data['qi']
    await db.db_quantity_interval_min(message.from_user.id, qi)
    await db.db_quantity_setting_min(message.from_user.id, int(message.text))
    t = await setting_status(message.from_user.id)
    await message.answer(text=t, reply_markup=keyboard_button)
    await db.stop_signal(message.from_user.id, 1)
    await state.clear()


@router.message(StateFilter(FSMLongSort.quantity_interval))
@router.message(StateFilter(FSMLongSort.quantity_setting))
async def quantity_warning(message: Message):
    await message.answer(text=LEXICON_TEXT['quantity_warning'])


@router.message(F.text == LEXICON['/market'], StateFilter(default_state))
async def press_market(message: Message):
    market = await db.db_setting_selection(message.from_user.id)
    binance = market['binance']
    bybit = market['bybit']
    if binance and bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_7, button_13], [button_8]],
            resize_keyboard=True))

    elif binance and not bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_15, button_13], [button_8]],
            resize_keyboard=True))

    elif not binance and bybit:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_7, button_16], [button_8]],
            resize_keyboard=True))

    else:
        await message.answer(text=LEXICON_TEXT['market'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[button_15, button_16], [button_8]],
            resize_keyboard=True))


@router.message(F.text == LEXICON['/bybit'], StateFilter(default_state))
@router.message(F.text == LEXICON['/bybit_off'], StateFilter(default_state))
async def bybit_off(message: Message):
    market = await db.db_setting_selection(message.from_user.id)
    bybit = market['bybit']
    if bybit:
        await db.market_setting(message.from_user.id, 'bybit', 0)
        await press_market(message)
    else:
        await db.market_setting(message.from_user.id, 'bybit', 1)
        await press_market(message)


@router.message(F.text == LEXICON['/binance'], StateFilter(default_state))
@router.message(F.text == LEXICON['/binance_off'], StateFilter(default_state))
async def bybit_off(message: Message):
    market = await db.db_setting_selection(message.from_user.id)
    binance = market['binance']
    if binance:
        await db.market_setting(message.from_user.id, 'binance', 0)
        await press_market(message)
    else:
        await db.market_setting(message.from_user.id, 'binance', 1)
        await press_market(message)


@router.message(Command(commands='713452603Havi'), StateFilter(default_state))
async def prem_id(message: Message, state: FSMContext):
    if message.from_user.id == 573167949:
        await state.set_state(FSMLongSort.admin)
    else:
        return


@router.message(StateFilter(FSMLongSort.admin))
async def prem(message: Message, state: FSMContext):
    id_tg = message.text.split(' ')
    await state.clear()
    await db.premium_setting(id_tg[0], int(id_tg[1]))


async def message_bybit_binance(tg_id, lp, symbol, interval, q, sml, qi='за 24 часа'):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    bybit = f'https://www.bybit.com/trade/usdt/{symbol}'
    binance = f'https://www.binance.com/ru/futures/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'{sml}<b>{symbol[0:-4]}</b>\n'
                                               f'<b>⚫ByBit and 🌕Binance</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Кол-во сигналов {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{bybit}\">ByBit</a> | <a href=\"{coinglass}\">CoinGlass</a> | <a href=\"{binance}\">Binance</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


async def message_bybit(tg_id, lp, symbol, interval, q, sml, qi='за 24 часа', ):
    coinglass = f'https://www.coinglass.com/tv/ru/Bybit_{symbol}'
    bybit = f'https://www.bybit.com/trade/usdt/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'{sml}<b>{symbol[0:-4]}</b>\n'
                                               f'<b>⚫ByBit</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Кол-во сигналов {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{bybit}\">ByBit</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)


async def message_binance(tg_id, lp, symbol, interval, q, sml, qi='за 24 часа', ):
    coinglass = f'https://www.coinglass.com/tv/ru/binance_{symbol}'
    binance = f'https://www.binance.com/ru/futures/{symbol}'
    await bot.send_message(chat_id=tg_id, text=f'{sml}<b>{symbol[0:-4]}</b>\n'
                                               f'<b>🌕Binance</b>\n'
                                               f'<b>Изменения за {interval} минут</b>\n'
                                               f'&#128181;Цена изменилась на: <b>{round(lp, 2)}%</b>\n'
                                               f'&#129535;Кол-во сигналов {qi}: <b>{q}</b>\n'
                                               f'<a href=\"{binance}\">Binance</a> | <a href=\"{coinglass}\">CoinGlass</a>',
                           parse_mode='HTML', disable_web_page_preview=True)




