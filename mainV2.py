from typing import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor

import aiosqlite
import re
import json
import os
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Dialog(StatesGroup):
    MainMenu = State()
    chose_group = State()
    get_homework = State()

bot = Bot(token="8465868766:AAHGtK98y2RzFmLC0kO4IQjNySZ95X1eJxM")
dp = Dispatcher(storage=MemoryStorage())

db: aiosqlite.Connection | None = None

localeUA_file = open("translate.json", "r", encoding="utf-8")
ua = json.load(localeUA_file)
localeUA_file.close()

async def startup():
    global db
    db = await aiosqlite.connect("database.db")
    await db.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        user_id INTEGER UNIQUE NOT NULL,
        class TEXT DEFAULT NULL,
        isAdmin BLOB DEFAULT 0
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS homework (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_username TEXT DEFAULT NULL,
        class TEXT NOT NULL,
        year_added INTENGER,
        mouth_added INTEGER,
        day_added INTENGER,
        time_added TEXT,
        due_day INTENGER,
        due_mouth INTENGER,
        due_year INTENGER,
        subject TEXT NOT NULL,
        text TEXT,
        file_path TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "group" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        schedule TEXT DEFAULT NULL,
        president_username TEXT DEFAULT NULL
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS subject (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        teacher_name TEXT DEFAULT NULL
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS group_subj (
        group_name TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        PRIMARY KEY (group_name, subject_name),
        FOREIGN KEY (group_name) REFERENCES "group"(group_name) ON DELETE CASCADE,
        FOREIGN KEY (subject_name) REFERENCES subject(name) ON DELETE CASCADE
    )
    """)
    await db.commit()
    try: 
        await dp.start_polling(bot)
    finally:
        await db.close()

async def get_user(id: int, mode: bool = False) -> aiosqlite.Row | bool:
    cur = await db.execute(
        "SELECT * FROM user WHERE user_id = ?",
        (id,))
    user = await cur.fetchone()
    await cur.close()
    if   user is not None and not mode: return True
    elif user is not None and mode: return user
    elif user is None: return False

async def IO_bound_map(func: Callable[[any], any], items: Iterable, /, *, max_concurrency: int = 50) -> list:
    semafore = asyncio.Semaphore(min(max_concurrency, len(items)))
    async def _wrap(item):
        async with semafore:
            return await func(item)

    tasks = [asyncio.create_task(_wrap(item)) for item in items]
    return await asyncio.gather(*tasks)

async def CPU_bound_map(items: list, func: Callable) -> list:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        tasks = [loop.run_in_executor(pool, func, item) for item in items]
        return await asyncio.gather(*tasks)

def make_button(data: dict) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=data["text"], callback_data=data["id"])

def build_keyboard(buttons: list[InlineKeyboardButton], columns:int=3):
    keyboard = [
            buttons[i:i+columns] for i in range(0, len(buttons), columns)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start", "menu"))
async def handler1(message: Message, state: FSMContext):
    print(2)
    if await get_user(message.from_user.id):
        data = [
            {"text": ua["Button_text"]["get_homework"], "id": "get_homework"},
            {"text": ua["Button_text"]["add_homework"], "id": "add_homework"}]
        buttons = await CPU_bound_map(data,make_button)
        print(buttons)
        await message.answer(ua["Texts"]["main_menu"], reply_markup=build_keyboard(buttons, columns=2))
        await state.set_state(Dialog.MainMenu)
    else:
        await db.execute(
                "INSERT INTO user (username, user_id) VALUES (?, ?)",
                (message.from_user.username, message.from_user.id))
        await db.commit()
        cur = await db.execute("SELECT group_name FROM 'group'")
        rows = await cur.fetchall()
        await cur.close()
        values = [row[0] for row in rows]
        data = [{"text": ua["GroupName"][value], "id":value} for value in values]
        buttons = await CPU_bound_map(data, make_button)
        await message.answer(ua["Texts"]["select_group"], reply_markup=build_keyboard(buttons))
        await state.set_state(Dialog.chose_group)

@dp.callback_query(StateFilter(Dialog.chose_group))
async def handler2(callback: CallbackQuery, state: FSMContext):
    await db.execute(
            "UPDATE user SET class = ? WHERE user_id = ?",
            (callback.data, callback.from_user.id))
    await db.commit()
    await callback.message.edit_text(ua["Texts"]["class_saved"])

@dp.callback_query(StateFilter(Dialog.MainMenu) | F.data == "get_homework")
async def handler3(callback: CallbackQuery, state: FSMContext):
    pass

asyncio.run(startup())




