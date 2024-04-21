from datetime import datetime

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher
from aiogram.types import InputMediaPhoto
from gameLogic.FuncsAndObjects.narrowly_focused import *
from gameLogic.logic import Hero
from random import choice, randint
from supportingFiles.connection import bot
from FuncsAndObjects.generals import get_time_in_right_format, get_photo_in_bytes
from CONSTANTS.POINTS_CONSTANTS import *


class DrugstoreStates(StatesGroup):
    enter_drugstore = State()
    failure = State()

    getting_task = State()
    accepting_task = State()

    success = State()


class Drugstore:
    X = 885
    Y = 110


    ITEM_SPAWN = [
        #  LEFT_DOWN, RIGHT_UP
        [(20, 170), (1860, 110)],
        [(580, 90), (640, 10)],
        [(1440, 290), (1480, 210)],
    ]


    BUTTON = types.InlineKeyboardButton(text="Взаимодействовать", callback_data="to_interact_with_drugstore")


    @staticmethod
    def get_keyboard(state):
        keyboard = types.InlineKeyboardMarkup()


        if state == DrugstoreStates.enter_drugstore:
            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_drugstore"),
                         types.InlineKeyboardButton(text="Да", callback_data="get_task"))
        elif state == DrugstoreStates.failure:
            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_drugstore"))
        elif state in (DrugstoreStates.getting_task, DrugstoreStates.success):
            keyboard.add(types.InlineKeyboardButton(text="Ок", callback_data="exit_from_drugstore"))


        return keyboard


    @staticmethod
    def get_reward(minutes):

        return 1200 // (minutes + 1)




def text_popup(map_file: io.BytesIO, popup_file_name: str, popup_coordinates: (int, int)) -> io.BytesIO:
    map_file = Image.open(map_file)
    popup_file = Image.open(popup_file_name)
    img = map_file.copy()
    img.paste(popup_file, popup_coordinates, mask=popup_file)

    img.convert("RGB")

    bytesio = io.BytesIO()

    img.save(bytesio, "PNG", quality=100)

    bytesio.seek(0)

    return bytesio


def spawn_item(user_hero: Hero) -> None:
    spawning_zone = choice(Drugstore.ITEM_SPAWN)

    x_min, y_max = spawning_zone[0]
    x_max, y_min = spawning_zone[1]

    x = randint(x_min, x_max)
    y = randint(y_min, y_max)

    task_time = get_time_in_right_format()

    user_hero.set_task(DrugstoreConst.NAME, task_time, SpawnPoint.NAME, x, y)





async def enter_drugstore_handler(call: types.CallbackQuery, state: FSMContext):
    user_hero = create_user_hero(call)

    task_time = user_hero.get_task_time("drugstore")

    if not task_time:
        await DrugstoreStates.enter_drugstore.set()

        keyboard = Drugstore.get_keyboard(DrugstoreStates.enter_drugstore)

        photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), DrugstoreConst.GREETING_FILE,
                                           DrugstoreConst.AVERAGE_POPUP_COORDINATES))

        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                     reply_markup=keyboard)

        photo = get_photo_in_bytes(DrugstoreConst.GREETING_FILE)

        x, y = DrugstoreConst.AVERAGE_POPUP_COORDINATES

        user_hero.set_popup(photo.read(), 0, x, y)
        user_hero.set_keyboard(keyboard)

    else:
        if user_hero.task_is_received("drugstore"):
            await DrugstoreStates.success.set()

            keyboard = Drugstore.get_keyboard(DrugstoreStates.success)

            photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), DrugstoreConst.SUCCESS_FILE,
                                               DrugstoreConst.AVERAGE_POPUP_COORDINATES))

            task_time_in_minutes = (datetime.utcnow() - user_hero.get_task_time("drugstore")).total_seconds() // 60

            reward_money = Drugstore.get_reward(task_time_in_minutes)

            user_hero.add_money(reward_money)

            user_hero.delete_task("drugstore")

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                         reply_markup=keyboard)

            photo = get_photo_in_bytes(DrugstoreConst.SUCCESS_FILE)

            x, y = DrugstoreConst.AVERAGE_POPUP_COORDINATES

            user_hero.set_popup(photo.read(), 0, x, y)
            user_hero.set_keyboard(keyboard)

        else:
            await DrugstoreStates.failure.set()

            keyboard = Drugstore.get_keyboard(DrugstoreStates.failure)

            photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), DrugstoreConst.FAILURE_FILE,
                                               DrugstoreConst.AVERAGE_POPUP_COORDINATES))

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                        reply_markup=keyboard)

            photo = get_photo_in_bytes(DrugstoreConst.FAILURE_FILE)

            x, y = DrugstoreConst.AVERAGE_POPUP_COORDINATES

            user_hero.set_popup(photo.read(), 0, x, y)
            user_hero.set_keyboard(keyboard)


async def exit_from_drugstore_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    user_hero = create_user_hero(call)

    keyboard = get_keyboard(user_hero)

    photo = InputMediaPhoto(get_map(call.from_user.id))

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.delete_popup_item()


async def getting_task_handler(call: types.CallbackQuery):
    await DrugstoreStates.getting_task.set()

    user_hero = create_user_hero(call)

    keyboard = Drugstore.get_keyboard(DrugstoreStates.getting_task)

    spawn_item(user_hero)

    photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), DrugstoreConst.TASK_FILE,
                                       DrugstoreConst.AVERAGE_POPUP_COORDINATES))


    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(DrugstoreConst.TASK_FILE)

    x, y = DrugstoreConst.AVERAGE_POPUP_COORDINATES

    user_hero.set_popup(photo.read(), 0, x, y)
    user_hero.set_keyboard(keyboard)


async def finding_item_handler(call: types.CallbackQuery):
    user_hero = create_user_hero(call)

    user_hero.receive_item_task("drugstore")

    keyboard = get_keyboard(user_hero)

    photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), DrugstoreConst.ITEM_POPUP,
                                       DrugstoreConst.ITEM_POPUP_COORDINATES))

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(DrugstoreConst.ITEM_POPUP)

    x, y = DrugstoreConst.ITEM_POPUP_COORDINATES

    user_hero.set_popup(popup_in_bytes=photo.read(), is_full_screen=0, x=x, y=y, delete_next_time=1)
    user_hero.set_keyboard(keyboard)


def register_drugstore_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(enter_drugstore_handler, text="to_interact_with_drugstore")
    dp.register_callback_query_handler(exit_from_drugstore_handler, text="exit_from_drugstore", state="*")
    dp.register_callback_query_handler(getting_task_handler, text="get_task", state=DrugstoreStates.enter_drugstore)
    dp.register_callback_query_handler(finding_item_handler, text="get_drugstore_item")
