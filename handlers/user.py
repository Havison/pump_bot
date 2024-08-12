from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from lexicon.lexicon import LEXICON, LEXICON_TEXT
from keyboards.keyboard_utils import create_inline_kb
import database as db
import datetime

storage = MemoryStorage()
router = Router()


class FSMLongSort(StatesGroup):
    changes_long = State() #состояние ожидание ввода роста в процентах
    interval_long = State() #состояние ожидание ввода интервала роста в минутах
    changes_short = State() #состояние ожидание ввода падения в процентах
    interval_short = State() #состояние ожидание ввода интервала падения в минутах


# Создаем объекты кнопок
button_1 = KeyboardButton(text=LEXICON['/setting'])
button_2 = KeyboardButton(text=LEXICON['/profile'])
button_3 = KeyboardButton(text=LEXICON['/help'])


# Создаем объект клавиатуры, добавляя в него кнопки
keyboard_button = ReplyKeyboardMarkup(keyboard=[[button_1, button_2, button_3]], resize_keyboard=True)


@router.message(CommandStart(), StateFilter(default_state)) # Этот хэндлер срабатывает на команду /start
async def process_start_command(message: Message):
    await db.db_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                            message.from_user.last_name, datetime.datetime.now())
    await message.answer(text=LEXICON['/start'],
                         reply_markup=keyboard_button)


@router.message(Command(commands='help'), StateFilter(default_state)) # Этот хэндлер срабатывает на команду /help
async def process_help_command(message: Message):
    await message.answer(text=LEXICON['/help'])


@router.message(F.text == LEXICON['/setting'], StateFilter(default_state))
@router.message(Command(commands='setting'), StateFilter(default_state)) # Этот хэндлер срабатывает на команду /setting
async def process_settings_command(message: Message):
    keyboard = create_inline_kb(2, 'LONG', 'SHORT')
    x = await db.db_result_long(message.from_user.id)
    y = await db.db_result_short(message.from_user.id)
    await message.answer(
        text=LEXICON_TEXT['setting_text'].format(changes_long=x[0], interval_long=x[1],
                                                 changes_short=y[0], interval_short=y[1]),
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'LONG', StateFilter(default_state))
async def process_long_press(callback_query: CallbackQuery, state: FSMContext):
    keyboard = create_inline_kb(1,'CHANEL')
    await callback_query.message.answer(
        text=LEXICON_TEXT['long_setting_changes'], reply_markup=keyboard)
    #устаналиваем состояние вводе роста
    await state.set_state(FSMLongSort.changes_long)


@router.message(StateFilter(FSMLongSort.changes_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 9999)
async def long_setting_changes(message: Message, state: FSMContext):
    await db.db_changes_long(message.from_user.id, int(message.text))
    await message.answer(text=LEXICON_TEXT['long_setting_changes'])
    await state.set_state(FSMLongSort.interval_long)


@router.message(StateFilter(FSMLongSort.interval_long),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 240)
async def long_setting_interval(message: Message, state: FSMContext):
    await db.db_interval_long(message.from_user.id, int(message.text))
    x = await db.db_result_long(message.from_user.id)
    await message.answer(text=LEXICON_TEXT['new_setting'].format(changes_long=x[0], interval_long=x[1]))
    await state.clear()


@router.message(StateFilter(FSMLongSort.changes_long))
async def warning_long_changes(message: Message):
    keyboard = create_inline_kb(1, 'CHANEL')
    await message.answer(text=LEXICON_TEXT['warning_long_changes'], reply_markup=keyboard)


@router.callback_query(F.data == 'SHORT', StateFilter(default_state))
async def process_short_press(callback_query: CallbackQuery, state: FSMContext):
    keyboard = create_inline_kb(1,'CHANEL')
    await callback_query.message.answer(
        text=LEXICON_TEXT['short_setting_changes'], reply_markup=keyboard)
    #устаналиваем состояние вводе роста
    await state.set_state(FSMLongSort.changes_short)


@router.message(StateFilter(FSMLongSort.changes_short),
                lambda x: isinstance(x.text, int) and -1 >= int(x.text) >= -9999)
async def short_setting_changes(message: Message, state: FSMContext):
    await db.db_changes_short(message.from_user.id, int(message.text))
    await message.answer(text=LEXICON_TEXT['setting_interval'])
    await state.set_state(FSMLongSort.interval_short)


@router.message(StateFilter(FSMLongSort.interval_short),
                lambda x: x.text.isdigit() and 1 <= int(x.text) <= 240)
async def long_setting_interval(message: Message, state: FSMContext):
    await db.db_interval_short(message.from_user.id, int(message.text))
    x = await db.db_result_long(message.from_user.id)
    y = await db.db_result_short(message.from_user.id)
    await message.answer(text=LEXICON_TEXT['new_setting'].format(changes_long=x[0], interval_long=x[1], changes_short=y[0], interval_short=y[1]))
    await state.clear()


@router.message(StateFilter(FSMLongSort.changes_short))
async def warning_long_changes(message: Message):
    keyboard = create_inline_kb(1, 'CHANEL')
    await message.answer(text=LEXICON_TEXT['warning_short_changes'], reply_markup=keyboard)


@router.message(StateFilter(FSMLongSort.interval_long))
@router.message(StateFilter(FSMLongSort.interval_short))
async def warning_interval(message: Message):
    keyboard = create_inline_kb(1, 'CHANEL')
    await message.answer(text=LEXICON_TEXT['warning_interval'], reply_markup=keyboard)


@router.callback_query(F.data == 'CHANEL', ~StateFilter(default_state))
async def process_chanel_press(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer(
        text=LEXICON_TEXT['chanel'])
















