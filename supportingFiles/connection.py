import sqlite3
from config import TOKEN
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from storages import SQLiteStorage


con = sqlite3.connect('rugalik.db')
cursor = con.cursor()

storage = SQLiteStorage("rugalik.db")

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=storage)
