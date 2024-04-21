import asyncio
import pickle
from functools import partial
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram import types
from aiogram.types import InputMediaPhoto
from aiogram.dispatcher import FSMContext, Dispatcher
from datetime import datetime, timedelta
from CONSTANTS.USER_CONSTANTS import User
from FuncsAndObjects.generals import get_photo_in_bytes
from gameLogic.logic import Hero
from random import choice, randint, shuffle
from FuncsAndObjects.narrowly_focused import create_user_hero, get_map
from supportingFiles.connection import bot, con, cursor
from .quiz import Quiz, QuizStates
from aiogram.dispatcher.filters.state import State, StatesGroup
from CONSTANTS.POINTS_CONSTANTS import QuizConst


class PartyStates(StatesGroup):
    playing = State()


class Party:
    POPUP_COORDINATES = (2, 230)

    WIN_MONEY = 1000

    FIRST_PLAYER_POPUP_FILE = "images/map/quiz/party/math_guy_welcome_equation.png"
    SECOND_PLAYER_POPUP_FILE = "images/map/quiz/party/math_guy_welcome_wait.png"

    PLAYER_FAILED_POPUP_FILE = "images/map/quiz/party/math_guy_you_failed.png"
    PLAYERS_FRIEND_FAILED_POPUP_FILE = "images/map/quiz/party/math_guy_friend_failed.png"

    PLAYER_SUCCESS_POPUP_FILE = "images/map/quiz/party/math_guy_regular_wait.png"
    PLAYERS_FRIEND_SUCCESS_POPUP_FILE = "images/map/quiz/party/math_guy_regular_equation.png"

    ALL_DONE = "images/map/quiz/party/math_guy_success.png"



    @staticmethod
    def math_task_popup(map_file, popup_file, fontname, equation=None):
        map_file = Image.open(map_file)
        popup_file = Image.open(popup_file)
        img = map_file.copy()
        img.paste(popup_file, (2, 230), mask=popup_file)
        draw = ImageDraw.Draw(img)
        fontname = ImageFont.truetype(fontname, 15)

        if equation:
            draw.text((89, 302), equation, font=fontname, fill=(233, 201, 41))

        bytesio = BytesIO()

        img.save(bytesio, format="PNG", quality=100)

        bytesio.seek(0)

        return bytesio

    @staticmethod
    def generate_math_task(num):
        actions = ("-", "/", "*", "+")

        min_number = -100
        max_number = 100

        while True:
            new_num = randint(min_number, max_number)

            if new_num:
                break

        res = str(new_num)

        for _ in range(num - 1):
            action = choice(actions)

            res += action

            while True:
                new_num = randint(min_number, max_number)

                if new_num:
                    break

            if new_num < 0:
                new_num = f"({new_num})"

            res += str(new_num)

        result = int(eval(res))

        false_options = [result - randint(-100, 100) for _ in range(3)]

        print(result)

        return result, false_options, res

    @staticmethod
    def get_keyboard_before_starting_game() -> types.InlineKeyboardMarkup:
        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(types.InlineKeyboardButton(text="Встать", callback_data="decline_game"),
                     types.InlineKeyboardButton(text="Готовность (0/2)", callback_data="accept_game"))

        return keyboard

    @staticmethod
    def get_keyboard_for_exit_only() -> types.InlineKeyboardMarkup:
        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(types.InlineKeyboardButton(text="Начать игру", callback_data="accept_game"))

        return keyboard

    def get_alacrity_keyboard(self, party_id) -> types.InlineKeyboardMarkup:
        ready_users_number = self.get_ready_users_number(party_id)

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(text=f"Готовность ({ready_users_number}/2)", callback_data="accept_game"))

        return keyboard

    @staticmethod
    def create_game(user_id: int) -> None:
        permitted_ids = list(set(cursor.execute("SELECT party_id FROM users_math_party").fetchall()))

        if permitted_ids:
            party_id = permitted_ids[-1][0] + 1
        else:
            party_id = 1

        cursor.execute("INSERT INTO users_math_party (user_id, party_id, is_ready) VALUES(?, ?, ?)",
                       (user_id, party_id, 0))
        con.commit()

    async def start_timer(self, user_id, other_user_id):
        await asyncio.sleep(10)

        is_ready = self.is_ready(user_id)

        if not is_ready:
            user_hero = Hero(user_id)

            user_hero.update_position(0)
            user_hero.update_coordinates(QuizConst.DEFAULT_X, QuizConst.DEFAULT_Y, QuizConst.DEFAULT_SIDE)

            await self.delete_user(user_id, move_to_entrance=True)

            photo = InputMediaPhoto(get_map(user_id))

            x, y = user_hero.get_coordinates()

            keyboard = Quiz().get_keyboard(x, y, user_id, 0)

            await bot.edit_message_media(chat_id=user_id, message_id=user_hero.get_message_id(), media=photo,
                                         reply_markup=keyboard)

            other_user_hero = Hero(other_user_id)

            photo = InputMediaPhoto(get_map(other_user_id))

            x, y = other_user_hero.get_coordinates()

            keyboard = Quiz().get_keyboard(x, y, other_user_id, 1)

            await bot.edit_message_media(chat_id=other_user_id, message_id=other_user_hero.get_message_id(),
                                         media=photo, reply_markup=keyboard)


    @staticmethod
    def add_user(user_id, players_ids: list) -> None:
        players_ids_for_function = players_ids.copy()

        players_ids_for_function.remove(user_id)


        cursor.execute("INSERT INTO users_math_party (user_id, is_ready, party_id) VALUES(?,?,?)", (user_id, 0,
                                                                                                    Party.get_party_id(players_ids_for_function[0])))
        con.commit()

    @staticmethod
    async def delete_user(user_id: int, move_to_entrance: bool = False) -> None:
        cursor.execute("DELETE FROM users_math_party WHERE user_id == ?", (user_id,))
        con.commit()

        if move_to_entrance:
            user_hero = Hero(user_id)

            user_hero.update_position(0)
            user_hero.update_coordinates(QuizConst.DEFAULT_X, QuizConst.DEFAULT_Y, QuizConst.DEFAULT_SIDE)

            photo = InputMediaPhoto(get_map(user_id))

            x, y = user_hero.get_coordinates()

            keyboard = Quiz().get_keyboard(x, y, user_id, 0)

            user_hero.set_state("QuizStates:enter_quiz")

            await bot.edit_message_media(chat_id=user_id, message_id=user_hero.get_message_id(), media=photo,
                                         reply_markup=keyboard)

    @staticmethod
    def is_ready(user_id: int) -> int:
        is_ready = cursor.execute("SELECT is_ready FROM users_math_party WHERE user_id == ?", (user_id,)).fetchone()[0]

        return is_ready

    @staticmethod
    def set_alacrity(user_id: int, alacrity: int) -> None:
        cursor.execute("UPDATE users_math_party SET is_ready == ? WHERE user_id == ?", (alacrity, user_id,))
        con.commit()

    @staticmethod
    def get_ready_users_number(party_id) -> int:
        alacrity = cursor.execute("SELECT is_ready FROM users_math_party WHERE party_id == ?", (party_id,)).fetchall()

        return len(list(filter(lambda x: x[0], alacrity)))

    @staticmethod
    def get_users(party_id):
        users = cursor.execute("SELECT user_id FROM users_math_party WHERE party_id = ?", (party_id, )).fetchall()

        return [u[0] for u in users]

    @staticmethod
    def set_list_of_passed_questions(user_id, list_of_passed_questions: list):
        pdata = pickle.dumps(list_of_passed_questions, pickle.HIGHEST_PROTOCOL)

        cursor.execute("UPDATE users_math_party SET list_of_passed_questions == ? WHERE user_id == ?", (pdata, user_id))
        con.commit()

    @staticmethod
    def get_list_of_passed_questions(user_id):
        list_of_passed_questions = cursor.execute("SELECT list_of_passed_questions FROM users_math_party WHERE "
                                                  "user_id == ?", (user_id ,)).fetchone()

        if list_of_passed_questions:
            list_of_passed_questions = pickle.loads(list_of_passed_questions[0])

            return list_of_passed_questions

    @staticmethod
    def user_has_failed(user_id):
        has_failed = cursor.execute("SELECT has_failed FROM users_math_party WHERE user_id == ?", (user_id, )).fetchone()[0]

        return has_failed

    @staticmethod
    def get_question_num(user_id):
        question_num = cursor.execute("SELECT question_num FROM users_math_party WHERE user_id = ?", (user_id, )).fetchone()[0]

        return question_num if question_num else 0

    @staticmethod
    def get_party_id(user_id):
        party_id = cursor.execute("SELECT party_id FROM users_math_party WHERE user_id = ?", (user_id,)).fetchone()[
                0]

        return party_id

    @staticmethod
    def set_question_num(user_id, question_num):
        cursor.execute("UPDATE users_math_party SET question_num == ? WHERE user_id == ?", (question_num, user_id))
        con.commit()


    def set_math_task_and_get_some_stuff(self, user_id: int, image: str):
        result, false_questions, equation = self.generate_math_task(3)

        keyboard = types.InlineKeyboardMarkup()

        options = false_questions + [result]

        shuffle(options)

        for num in options:
            if num == result:
                keyboard.add(types.InlineKeyboardButton(text=str(num), callback_data=f"right_answer"))
            else:
                keyboard.add(types.InlineKeyboardButton(text=str(num), callback_data=f"false_answer"))

        photo = InputMediaPhoto(self.math_task_popup(get_map(user_id), image, User.NICKNAME_FONT, equation))

        return keyboard, photo


    async def start_timer_for_math_task(self, user_id, other_user_id):
        await asyncio.sleep(15)

        user_hero = Hero(user_id, update_last_action_time=False)

        last_action_time = user_hero.get_last_action_time()


        if datetime.utcnow() - timedelta(seconds=14) > last_action_time:
            await self.delete_user(user_id, move_to_entrance=True)

            other_user_hero = Hero(other_user_id)

            photo = InputMediaPhoto(get_map(other_user_id))

            x, y = other_user_hero.get_coordinates()

            keyboard = Quiz().get_keyboard(x, y, other_user_id, 1)

            other_user_hero.set_state("QuizStates:enter_quiz")

            self.set_alacrity(other_user_id, 0)

            await bot.edit_message_media(chat_id=other_user_id, message_id=other_user_hero.get_message_id(),
                                         media=photo, reply_markup=keyboard)




async def sit_at_handler(call: types.CallbackQuery, state: FSMContext):
    coordinates_string, side = call.data.replace("sit_at: ", "").split("; ")

    coordinates = [int(i) for i in coordinates_string.split(", ")]

    x, y = coordinates


    user_hero = create_user_hero(call)

    user_hero.update_position(1)

    user_hero.update_coordinates(x, y, side, check=False)

    quiz = Quiz()

    players_id = quiz.alacrity_checker(user_hero.user_id)

    if players_id:
        Party.add_user(user_hero.user_id, players_id)

        for user_id in players_id:

            photo = InputMediaPhoto(get_map(user_id))

            keyboard = Party.get_keyboard_before_starting_game()

            user_hero = Hero(user_id)

            await bot.edit_message_media(chat_id=user_id, message_id=user_hero.get_message_id(), media=photo,
                                         reply_markup=keyboard)

            async with state.proxy() as container:
                container["players_id"] = players_id

    else:
        Party.create_game(user_hero.user_id)

        photo = InputMediaPhoto(get_map(user_hero.user_id))

        keyboard = quiz.get_keyboard(x, y, user_hero.user_id, is_sitting=1)

        await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                     reply_markup=keyboard)


async def stand_up_handler(call: types.CallbackQuery):
    user_hero = create_user_hero(call)

    user_hero.update_position(0)

    x, y = user_hero.get_coordinates()

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    await Party.delete_user(user_hero.user_id)

    quiz = Quiz()

    keyboard = quiz.get_keyboard(x, y, user_hero.user_id)

    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.delete_popup_item()

    user_hero.set_keyboard(keyboard)


async def press_alacrity_button_handler(call: types.CallbackQuery, state: FSMContext):
    user_hero = create_user_hero(call)

    if Party.is_ready(user_hero.user_id):
        return

    party_id = Party.get_party_id(user_hero.user_id)

    ready_users_number = Party.get_ready_users_number(party_id)

    players_id = Party.get_users(Party.get_party_id(user_hero.user_id))

    Party.set_alacrity(user_hero.user_id, 1)

    if ready_users_number == 0:
        players_id.remove(user_hero.user_id)

        other_player_id = players_id[0]

        party = Party()

        photo = InputMediaPhoto(get_map(user_hero.user_id))  # Что-то другое здесь должно быть

        keyboard = party.get_alacrity_keyboard(party_id)

        await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                     reply_markup=keyboard)

        other_hero = Hero(other_player_id)
        photo = InputMediaPhoto(get_map(other_player_id))

        await bot.edit_message_media(chat_id=other_player_id, message_id=other_hero.get_message_id(), media=photo,
                                     reply_markup=keyboard)

        await party.start_timer(other_player_id, user_hero.user_id)

    else:
        first = choice(players_id)

        first_hero = Hero(first)

        party = Party()

        keyboard, photo = party.set_math_task_and_get_some_stuff(first, party.FIRST_PLAYER_POPUP_FILE)

        X, Y = Party.POPUP_COORDINATES

        first_hero.set_popup(get_photo_in_bytes(party.FIRST_PLAYER_POPUP_FILE).read(), False, X, Y)
        first_hero.set_keyboard(keyboard)

        await bot.edit_message_media(chat_id=first, message_id=first_hero.get_message_id(), media=photo,
                                     reply_markup=keyboard)

        players_id.remove(first)

        second = players_id[0]

        photo = InputMediaPhoto(Party.math_task_popup(get_map(second), Party.SECOND_PLAYER_POPUP_FILE, User.NICKNAME_FONT))

        second_hero = Hero(second)

        await bot.edit_message_media(chat_id=second, message_id=second_hero.get_message_id(), media=photo)

        second_hero.set_popup(get_photo_in_bytes(Party.SECOND_PLAYER_POPUP_FILE).read(), False, X, Y)
        second_hero.set_keyboard(types.InlineKeyboardMarkup())

        first_hero.set_state("PartyStates:playing")
        second_hero.set_state("PartyStates:playing")

        await Party().start_timer_for_math_task(first, second)


async def check_answer(call: types.CallbackQuery, state: FSMContext):
    user_hero = create_user_hero(call)

    user_hero.update_last_action_time()

    players_id = Party.get_users(Party.get_party_id(user_hero.user_id))

    players_id.remove(user_hero.user_id)

    other_id = players_id[0]
    other_user_hero = Hero(other_id)
    other_question_num = Party.get_question_num(other_id)

    if call.data == "right_answer":
        question_num = Party.get_question_num(user_hero.user_id)


        if question_num == 5 and other_question_num == 5:
            user_hero.set_state("QuizStates:enter_quiz")
            other_user_hero.set_state("QuizStates:enter_quiz")

            user_hero.add_money(Party.WIN_MONEY)
            other_user_hero.add_money(Party.WIN_MONEY)

            photo = InputMediaPhoto(Party.math_task_popup(get_map(user_hero.user_id), Party.ALL_DONE, User.NICKNAME_FONT))

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=user_hero.get_message_id(), media=photo)

            photo = InputMediaPhoto(Party.math_task_popup(get_map(other_id), Party.ALL_DONE, User.NICKNAME_FONT))

            await bot.edit_message_media(chat_id=other_id, message_id=other_user_hero.get_message_id(), media=photo)

            await asyncio.sleep(5)

            await Party.delete_user(user_hero.user_id, move_to_entrance=True)
            await Party.delete_user(other_user_hero.user_id, move_to_entrance=True)

            user_hero.delete_popup_item()
            user_hero.delete_keyboard()

            other_user_hero.delete_popup_item()
            other_user_hero.delete_keyboard()
        else:
            keyboard, photo = Party().set_math_task_and_get_some_stuff(other_id, Party.PLAYERS_FRIEND_SUCCESS_POPUP_FILE)

            if question_num != 5:
                Party.set_question_num(user_hero.user_id, question_num + 1)

            await bot.edit_message_media(chat_id=other_id, message_id=other_user_hero.get_message_id(), media=photo,
                                         reply_markup=keyboard)

            X, Y = Party.POPUP_COORDINATES

            other_user_hero.set_popup(get_photo_in_bytes(Party.PLAYERS_FRIEND_SUCCESS_POPUP_FILE).read(), False, X, Y)
            other_user_hero.set_keyboard(keyboard)

            photo = InputMediaPhoto(Party.math_task_popup(get_map(other_id), Party.PLAYER_SUCCESS_POPUP_FILE, User.NICKNAME_FONT))

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=user_hero.get_message_id(),
                                         media=photo)

            user_hero.set_popup(get_photo_in_bytes(Party.PLAYER_SUCCESS_POPUP_FILE).read(), False, X, Y)
            user_hero.set_keyboard(types.InlineKeyboardMarkup())

            await Party().start_timer_for_math_task(other_id, user_hero.user_id)
    else:
        Party.set_question_num(user_hero.user_id, 0)
        Party.set_question_num(other_id, 0)

        photo = InputMediaPhoto(Party.math_task_popup(get_map(user_hero.user_id), Party.PLAYER_FAILED_POPUP_FILE, User.NICKNAME_FONT))

        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=user_hero.get_message_id(), media=photo)

        user_hero.set_popup(Party.math_task_popup(get_map(user_hero.user_id),
                                                  Party.PLAYER_FAILED_POPUP_FILE, User.NICKNAME_FONT).read(), True)
        user_hero.set_keyboard(types.InlineKeyboardMarkup())

        keyboard, photo = Party().set_math_task_and_get_some_stuff(other_id, Party.PLAYERS_FRIEND_FAILED_POPUP_FILE)

        await bot.edit_message_media(chat_id=other_id, message_id=other_user_hero.get_message_id(), media=photo,
                                     reply_markup=keyboard)

        other_user_hero.set_popup(Party.math_task_popup(get_map(user_hero.user_id),
                                                  Party.PLAYER_FAILED_POPUP_FILE, User.NICKNAME_FONT).read(), True)

        await Party().start_timer_for_math_task(other_id, user_hero.user_id)


def register_party_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(sit_at_handler, text_contains="sit_at", state=QuizStates.enter_quiz)
    dp.register_callback_query_handler(stand_up_handler, text_contains="stand_up", state=QuizStates.enter_quiz)
    dp.register_callback_query_handler(press_alacrity_button_handler, text_contains="accept_game", state=QuizStates.enter_quiz)
    dp.register_callback_query_handler(check_answer, text_contains="answer", state=PartyStates.playing)
