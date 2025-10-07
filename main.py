import sqlite3
import telebot
import re
import json
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

bot = telebot.TeleBot("8465868766:AAHGtK98y2RzFmLC0kO4IQjNySZ95X1eJxM")

local = json.load(open("translate.json", "r", encoding="utf-8"))

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
               year_added INTEGER,
               mouth_added INTEGER,
               day_added INTEGER,
               due_day INTEGER,
               due_mouth INTEGER,
               due_year INTEGER,
               subject TEXT NOT NULL,
               text TEXT,
               file_path TEXT
               )
               """)
    db.execute("""
               CREATE TABLE IF NOT EXISTS group (
               id INTENGER PRIMARY KEY AUTOINCREMENT,
               group TEXT DEFAULT NULL,
               group_number INTENGER DEFAULT 0,
               schedule TEXT DEFAULT NULL,
               president INTENGER DEFAULT 0
               )
               """)
    db.execute("""
               CREATE TABLE IF NOT EXISTS lessons (
               id INTENGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               teacher_name TEXT,
               teacher_class INTENGER DEFAULT 0
               )
               """)
    db.commit()

def check_user(msg: Message | CallbackQuery) -> sqlite3.Row:
    if isinstance(msg, Message): 
        id = msg.from_user.id
        username = msg.from_user.username
    elif isinstance(msg, User): 
        id = msg.id
        username = msg.username

    with sqlite3.connect("database.db") as db:
        user = db.execute(
                "SELECT * FROM user WHERE user_id = ?", 
                (id,)).fetchone()
        if user: return user
        else:
            db.execute(
                    "INSERT INTO user (username, user_id) VALUES (?, ?)", 
                    (username, id,))
            db.commit()
            return user

def create_keyboard(buttons: list[dict], row_width: int = 2) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    for i in range(0, len(buttons), row_width):
        row_buttons = [
            InlineKeyboardButton(text=btn["name"], callback_data=btn["data"])
            for btn in buttons[i:i+row_width]
        ]
        keyboard.row(*row_buttons)
    return keyboard


@bot.message_handler(commands=["start"])
def handler1(message):
    check_user(message)
    bot.send_message(
            message.chat.id, 
            local["/start_message"], 
            reply_markup=create_keyboard([
                                    {"name": local["Button_text"]["get_homework"], 
                                     "data": "gethomework"},
                                    {"name": local["Button_text"]["add_homework"], 
                                     "data": "addhomework"}]))
    

@bot.callback_query_handler(func=lambda call: call.data == "gethomework")
def handler3(call):
    with sqlite3.connect("database.db") as db:
        user_class = db.execute(
                "SELECT class FROM user WHERE user_id = ?", 
                (call.from_user.id,)).fetchone()[0]
        keys=[]

        if user_class == None: 
            for item in list(local["class_list"].keys()):
                keys.append({"name": local["class_list"][item], "data": item})
            bot.send_message(
                    call.from_user.id, 
                    local["texts"]["select_class"], 
                    reply_markup=create_keyboard(keys))
            
        elif user_class in list(local["class_list"].keys()):
            for item in list(local["subjectList"].keys()):
                keys.append({"name": local["subjectList"][item], "data": f"{item}.get")
            bot.send_message(
                    call.message.chat.id, 
                    local["texts"]["Choose_subject"], 
                    reply_markup=create_keyboard(keys)
                    }
            

@bot.callback_query_handler(func=lambda call: call.data == "addhomework")
def handler6(call):
    bot.send_message(call.message.chat.id, local["Not_Completed"])
    pass


@bot.callback_query_handler(func: lambda call: call.data )
def handler4(call):
    with sqlite3.connect("database.db") as db:
        db.execute(
            "UPDATE user SET class = ? WHERE user_id = ?", 
            (call.data, call.from_user.id))
        db.commit()
        bot.send_message(
            call.from_user.id,
            local["texts"]["class_saved"])

@bot.callback_query_handler(func: lambda call: call.data in list(local["subjectList"].keys()))
def handler7(call):
    with sqlite3.sqlite3.connect("database.db") as db:
        mouths = db.execute(
            "SELECT due_mouth FROM homework WHERE class = ?, subject = ?", 
            (db.execute(
                "SELECT class FROM user WHERE user_id = ?",
                (call.from_user.id)
                ), call.data 
             )

bot.polling(non_stop=True)
