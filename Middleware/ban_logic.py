from aiogram.types import InputMediaPhoto
from supportingFiles.connection import cursor, con, bot
from aiogram import types, Dispatcher, exceptions
from CONSTANTS.USER_CONSTANTS import User
from CONSTANTS.POINTS_CONSTANTS import Prison
from datetime import datetime, timedelta
from gameLogic.FuncsAndObjects.narrowly_focused import get_keyboard, get_map, create_user_hero
from gameLogic.FuncsAndObjects.generals import get_photo_in_bytes, get_time_in_right_format


def get_user_times_exceeded(user_id: int) -> int:
    times_exceeded = cursor.execute("SELECT times_exceeded FROM users_ban WHERE user_id = ?", (user_id,)).fetchone()[0]

    return times_exceeded


def update_user_times_exceeded(user_id: int) -> None:
    cursor.execute("UPDATE users_ban SET times_exceeded = times_exceeded + 1 WHERE user_id =?", (user_id, ))
    con.commit()


def check_user_ban(user_id: int) -> bool:
    ban_time = cursor.execute("SELECT ban_time FROM users_ban WHERE user_id =?", (user_id,)).fetchone()[0]

    datetime_object = datetime.strptime(ban_time, "%Y-%m-%d %H:%M:%S")

    if datetime_object.utcnow() - timedelta(seconds=User.BAN_TIME_IN_SECONDS) >= datetime_object:
        cursor.execute("UPDATE users_ban SET ban_time = ?, times_exceeded = ? WHERE user_id =?", ("", 0, user_id,))
        con.commit()

        return True

    return False


async def ban_user(user_id: int, call: types.CallbackQuery):
    cursor.execute("UPDATE users_ban SET ban_time =? WHERE user_id =?", (get_time_in_right_format(), user_id))
    con.commit()

    user_hero = create_user_hero(call)

    photo = InputMediaPhoto(get_photo_in_bytes(Prison.PRISON_FILE))

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton(text="⟳", callback_data="prison_update"))

    try:
        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id,
                                     media=photo, reply_markup=keyboard)
    except exceptions.MessageNotModified:
        pass


async def update_prison(call: types.CallbackQuery):
    if check_user_ban(call.from_user.id):
        user_hero = create_user_hero(call)

        keyboard = get_keyboard(user_hero)

        photo = InputMediaPhoto(get_map(call.from_user.id))

        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id,
                                     media=photo, reply_markup=keyboard)


def register_ban_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(update_prison, text="prison_update", state="*")
