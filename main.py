import sqlite3
import asyncio
import telebot
import lib
import re
import json
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

bot = telebot.TeleBot("8465868766:AAHGtK98y2RzFmLC0kO4IQjNySZ95X1eJxM")

localization = json.load(open("translate.json", "r", encoding="utf-8"))

lessonsList = {
    "Monday": [
        localization["subjectList"]["math"],
        localization["subjectList"]["biologia"],
        localization["subjectList"]["ukranian_literature"],
        localization["subjectList"]["CE"]
    ],
    "Tuesday": [
        localization["subjectList"]["english_language"],
        localization["subjectList"]["literature"],
        localization["subjectList"]["IT"]
    ],
    "Wednesday": [
        localization["subjectList"]["math"],
        localization["subjectList"]["geographia"],
        localization["subjectList"]["physics"],
        localization["subjectList"]["PE"]
    ],
    "Thursday": [
        localization["subjectList"]["idk"],
        localization["subjectList"]["ukranian_language"],
        localization["subjectList"]["ukranian_history"]
    ],
    "Friday": [
        localization["subjectList"]["PE"],
        localization["subjectList"]["world_history"],
        localization["subjectList"]["defence"]
    ]
}

def setup():
    with sqlite3.connect("database.db") as db:
        db.execute("""
                     CREATE TABLE IF NOT EXISTS user (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE,
                     user_id INTEGER UNIQUE,
                     class TEXT DEFAULT NULL,
                     isAdmin BLOB DEFAULT 0
                     )
                     """)
        db.execute("""
                     CREATE TABLE IF NOT EXISTS homework (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     class TEXT DEFAULT NULL,
                     date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                     due_date TEXT DEFAULT NULL,
                     subject TEXT NOT NULL,
                     text TEXT,
                     file_path TEXT
                     )
                     """)
        db.commit()

def get_or_create_user(msg: Message | CallbackQuery) -> sqlite3.Row:
    if isinstance(msg, Message): 
        id = msg.from_user.id
        username = msg.from_user.username
    elif isinstance(msg, User): 
        id = msg.id
        username = msg.username

    with sqlite3.connect("database.db") as db:
        print(id)
        cursor = db.execute("SELECT * FROM user WHERE user_id = ?", (id,))
        user = cursor.fetchone()
    
        if user:
            return user
        else:
            db.execute("INSERT INTO user (username, user_id) VALUES (?, ?)", (username, id,))
            db.commit()
            return user

def create_keyboard(buttons: list[dict], row_width: int = 2) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    for i in range(0, len(buttons), row_width):
        row_buttons = [
            InlineKeyboardButton(text=btn["name"], callback_data=btn["data"])
            for btn in buttons[i:i+row_width]
        ]
        keyboard.row(*row_buttons)  # кладём несколько кнопок в одну строку
    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    get_or_create_user(message)
    keyboard = create_keyboard([
        {"name": "Get homework", "data": "gethomework"},
        {"name": "Add homework", "data": "addhomework"}])
    bot.send_message(message.chat.id, "Hello, this message wait localization", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def echo(msg):
    bot.reply_to(msg, msg.text)

@bot.callback_query_handler()
def callbacks(call):
    with sqlite3.connect("database.db") as db:
        if call.data == "gethomework":
            user_class = db.execute("SELECT class FROM user WHERE user_id = ?", (call.from_user.id,)).fetchone()[0]
            if user_class == None:
                keys=[]
                for item in list(localization["class_list"].keys()):
                    keys.append({"name": localization["class_list"][item], "data": item})
                bot.send_message(call.from_user.id, localization["select_class"], reply_markup=create_keyboard(keys))

            elif user_class in list(localization["class_list"].keys()):
                keys=[]
                for item in list(localization["subjectList"].keys()):
                    keys.append({"name": localization["subjectList"][item], "data": item})
                keyboard = create_keyboard(keys)
                bot.send_message(call.message.chat.id, "Chose subject", reply_markup=keyboard)

        if call.data in list(localization["class_list"].keys()):
            db.execute("UPDATE user SET class = ? WHERE user_id = ?", (call.data, call.from_user.id))
            db.commit()
            bot.send_message(call.from_user.id, localization["class_saved"])


setup()
bot.polling(non_stop=True)
