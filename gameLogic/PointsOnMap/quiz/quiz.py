from datetime import datetime

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher
from aiogram.types import InputMediaPhoto
from aiogram import exceptions

from gameLogic.FuncsAndObjects.narrowly_focused import *
from gameLogic.logic import Hero
from supportingFiles.connection import bot
from FuncsAndObjects.generals import get_time_in_right_format
from CONSTANTS.POINTS_CONSTANTS import *


class QuizStates(StatesGroup):
    enter_quiz = State()


class Quiz:
    BUTTON = types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_quiz")

    EXIT_BUTTON = types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_quiz")

    STAND_UP_BUTTON = types.InlineKeyboardButton(text="Встать", callback_data="stand_up")

    CHAIRS_COORDINATES = [{(135, 80): types.InlineKeyboardButton(text="Сесть",
                                                                 callback_data="sit_at: 135, 80; left"),
                           (55, 80): types.InlineKeyboardButton(text="Сесть",
                                                                callback_data="sit_at: 55, 80; right"), },
                          {(215, 80): types.InlineKeyboardButton(text="Сесть",
                                                                 callback_data="sit_at: 215, 80; right"),
                           (295, 80): types.InlineKeyboardButton(text="Сесть",
                                                                 callback_data="sit_at: 295, 80; left"), }]

    def get_keyboard(self, x: int, y: int, self_id: int, is_sitting: int | bool = 0) -> \
            types.InlineKeyboardMarkup:

        keyboard = types.InlineKeyboardMarkup()

        button_ = None

        if is_sitting:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬆', callback_data='#'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))
        else:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬆', callback_data='up'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))

        step = User.STEP_IN_PIXELS

        if 0 <= abs(QuizConst.DEFAULT_X - x) <= step + 1 and 0 <= abs(QuizConst.DEFAULT_Y - y) <= step + 1:
            button_ = self.EXIT_BUTTON
        else:
            for chair_buttons_data in self.CHAIRS_COORDINATES:
                for coordinates, chair_button in chair_buttons_data.items():
                    x_, y_ = coordinates
                    if abs(x_ - x) <= step and abs(y_ - y) <= step:
                        if not is_sitting:
                            if check_coordinates(x_, y_, self_id, QuizConst.NAME):
                                button_ = chair_button
                        else:
                            button_ = self.STAND_UP_BUTTON
                        break

        if button_:
            if is_sitting:
                keyboard.add(types.InlineKeyboardButton(text='⬅', callback_data='#'),
                             button_,
                             types.InlineKeyboardButton(text='➡', callback_data='#'))
            else:
                keyboard.add(types.InlineKeyboardButton(text='⬅', callback_data='left'),
                             button_,
                             types.InlineKeyboardButton(text='➡', callback_data='right'))
        else:
            keyboard.add(types.InlineKeyboardButton(text='⬅', callback_data='left'),
                         types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='➡', callback_data='right'))

        if is_sitting:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬇', callback_data='#'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))
        else:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬇', callback_data='down'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))

        return keyboard

    def alacrity_checker(self, user_call_id: int) -> list or None:
        users_sitting = {}

        for index, chair_button_data in enumerate(self.CHAIRS_COORDINATES):
            for coordinates in chair_button_data.keys():
                x, y = coordinates

                user_id = cursor.execute("SELECT user_id FROM users_coordinates WHERE location_name == ? and x == ? and y == ? and is_sitting == ?",
                                         (QuizConst.NAME, x, y, 1)).fetchone()


                if user_id:
                    users_sitting[index] = users_sitting.get(index, []) + [user_id[0]]



        for players_id in users_sitting.values():
            if len(players_id) == 2 and user_call_id in players_id:
                return players_id


async def enter_quiz_handler(call: types.CallbackQuery):
    await QuizStates.enter_quiz.set()

    user_hero = create_user_hero(call)

    user_hero.update_location(QuizConst.NAME)

    user_hero.update_coordinates(QuizConst.DEFAULT_X, QuizConst.DEFAULT_Y, QuizConst.DEFAULT_SIDE)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    quiz = Quiz()

    keyboard = quiz.get_keyboard(QuizConst.DEFAULT_X, QuizConst.DEFAULT_Y, user_hero.user_id)

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.set_keyboard(keyboard)


async def move_in_quiz_handler(call: types.CallbackQuery):
    user_hero = create_user_hero(call)


    user_hero.update_position(0)

    side = call.data

    x, y = user_hero.get_coordinates()

    user_hero.update_coordinates(x, y, side)

    quiz = Quiz()

    x, y = user_hero.get_coordinates()

    keyboard = quiz.get_keyboard(x, y, user_hero.user_id)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    try:
        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                     reply_markup=keyboard)
    except (exceptions.MessageNotModified, exceptions.BadRequest) as e:
        print(e)

    user_hero.set_keyboard(keyboard)


async def exit_from_quiz_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    user_hero = create_user_hero(call)

    user_hero.update_location(SpawnPoint.NAME)

    user_hero.update_coordinates(QuizConst.X, QuizConst.Y, "down")

    keyboard = get_keyboard(user_hero)

    photo = InputMediaPhoto(get_map(call.from_user.id))

    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.delete_popup_item()
    user_hero.set_keyboard(keyboard)


def register_quiz_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(enter_quiz_handler, text="enter_quiz", state=None)

    dp.register_callback_query_handler(move_in_quiz_handler, lambda call:
    call.data in ["up", "down", "left", "right"], state=QuizStates.enter_quiz)

    dp.register_callback_query_handler(exit_from_quiz_handler, text="exit_from_quiz", state=QuizStates.enter_quiz)
