import io
from supportingFiles.connection import cursor
from gameLogic.logic import Hero
from aiogram import types
from CONSTANTS.POINTS_CONSTANTS import list_with_partial_points_data, items_tasks_data
from CONSTANTS.USER_CONSTANTS import *
from random import choice, randint
from FuncsAndObjects.generals import is_banned
from PIL import Image


# Отсюда нельзя ничего импортировать в gameLogic.logic
def get_map(user_id: int) -> io.BytesIO:
    users_heroes_in_db = [Hero(i[0], update_last_action_time=False)
                          for i in cursor.execute("SELECT id FROM users").fetchall()]

    photo = None

    user_hero = Hero(user_id)

    user_location = user_hero.get_location()

    users_id_in_db = [i.user_id for i in sorted(users_heroes_in_db, key=lambda u: u.get_last_action_time())
                      if i.get_location() == user_location]

    for index, user_id_ in enumerate(users_id_in_db):
        current_coordinates = cursor.execute("SELECT x, y, side FROM users_coordinates WHERE user_id ==?",
                                             (user_id_,)).fetchone()

        x, y, side = current_coordinates

        username = cursor.execute("SELECT username FROM users WHERE id == ?", (user_id_,)).fetchone()[0]

        if user_id_ == user_id:
            user_hero = Hero(user_id)

            if not photo:
                if user_hero.get_location() == user_hero.get_task_location():

                    photo = user_hero.spawn_task_item(Image.open(user_hero.get_location().SPAWN_FILE))
                    photo = user_hero.spawn(x, y, photo)
                else:
                    photo = user_hero.spawn(x, y, Image.open(user_hero.get_location().SPAWN_FILE))
            else:
                photo = user_hero.spawn_task_item(photo)
                photo = user_hero.spawn(x, y, photo)
            continue

        user_hero = Hero(user_id_, update_last_action_time=False)

        if not user_hero.check_time():
            continue

        if not is_banned(user_id):
            continue

        if index == 0:

            photo = user_hero.spawn(x, y)
        else:
            if not photo:
                photo = user_hero.spawn(x, y)

            else:
                photo = user_hero.spawn(x, y, photo)


        photo = user_hero.spawn_nickname(photo, User.NICKNAME_FONT, x, y)

    user_hero = Hero(user_id, get_username(user_id))

    current_coordinates = cursor.execute("SELECT x, y, side FROM users_coordinates WHERE user_id ==?",
                                         (user_id,)).fetchone()

    x = current_coordinates[0]

    photo = user_hero.zoom_to_player(photo, x)
    return photo


def get_username(user_id: int) -> str:
    username = cursor.execute("SELECT username FROM users WHERE id == ?", (user_id,)).fetchone()[0]

    return username


def get_keyboard(user_hero: Hero) -> types.InlineKeyboardMarkup:
    """Получение кнопок взаимодействия с ботом"""
    def get_point_button():
        for data in list_with_partial_points_data:
            button_ = data[0]
            point_x, point_y = data[1]
            if (abs(point_x - x) <= step * 2 or abs(x - point_x) <= step * 2) and (abs(point_y - y) <= step * 2
                                                                                   or abs(y - point_y) <= step * 2):
                button = button_
                break
        else:
            button = None

        return button


    x, y = user_hero.get_coordinates()

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                 types.InlineKeyboardButton(text='⬆', callback_data='up'),
                 types.InlineKeyboardButton(text='�', callback_data='None'))

    step = User.STEP_IN_PIXELS

    task_name = user_hero.get_task_name()

    if task_name:
        is_received = user_hero.task_is_received(task_name)

        if not is_received:
            item_button = items_tasks_data.get(task_name)

            item_x, item_y = user_hero.get_task_item_coordinates(task_name)
            if (abs(item_x - x) <= step * 2 or abs(x - item_x) <= step * 2) and (abs(item_y - y) <= step * 2
                                                                                 or abs(y - item_y) <= step * 2):
                button = item_button
            else:
                button = get_point_button()
        else:
            button = get_point_button()

    else:
        button = get_point_button()

    if button:
        keyboard.add(types.InlineKeyboardButton(text='⬅', callback_data='left'),
                     button,
                     types.InlineKeyboardButton(text='➡', callback_data='right'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='⬅', callback_data='left'),
                     types.InlineKeyboardButton(text='�', callback_data='None'),
                     types.InlineKeyboardButton(text='➡', callback_data='right'))

    keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                 types.InlineKeyboardButton(text='⬇', callback_data='down'),
                 types.InlineKeyboardButton(text='�', callback_data='None'))

    return keyboard


def get_keyboard_for_choosing_color() -> types.InlineKeyboardMarkup:
    color_data = [{"1": "red", "2": "yellow", "3": "orange"},
                  {"4": "green", "5": "blue", "6": "purple"},
                  {"7": "pink", "8": "dark", "9": "white"},
                  {"10": "skin", "11": "brown", "12": "cyan"}]

    keyboard = types.InlineKeyboardMarkup()

    for row in color_data:
        keyboard.add(*[types.InlineKeyboardButton(text=key, callback_data=value) for key, value in row.items()])

    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))

    return keyboard


def check_coordinates(x: int, y: int, self_id: int, location_name: str) -> bool:
    users = cursor.execute("SELECT user_id FROM users_coordinates WHERE location_name = ?", (location_name,)).fetchall()

    for user_id in users:
        if user_id == self_id:
            continue

        user_id = user_id[0]

        user_hero = Hero(user_id, update_last_action_time=False)

        if (x, y) == user_hero.get_coordinates():
            is_sitting = cursor.execute("SELECT is_sitting FROM users_coordinates WHERE user_id = ?",
                                        (user_id,)).fetchone()[0]

            if not user_hero.check_time():
                user_hero.update_position(0)
                return True


            if is_sitting:
                return False

    return True


def create_user_hero(call: types.CallbackQuery):
    user_id = call.from_user.id

    return Hero(user_id)

