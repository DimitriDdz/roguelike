import asyncio
from random import randint

from PIL import ImageDraw, ImageFont
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from CONSTANTS.POINTS_CONSTANTS import LuckPointConst
from FuncsAndObjects.narrowly_focused import *
from FuncsAndObjects.generals import get_photo_in_bytes
import io
from supportingFiles.connection import bot
from .luck_keepers_house import LuckKeepersHouseStates, LuckKeepersHouse


class LuckPointStages(StatesGroup):
    greeting = State()

    failed = State()

    first_throw = State()
    second_throw = State()
    third_throw = State()


    stage_data = {
        1: first_throw,
        2: second_throw,
        3: third_throw
    }


    async def set_throw_stage(self, throw_num: int) -> None:
        await self.stage_data.get(throw_num).set()


class LuckPoint:
    @staticmethod
    def get_keyboard(throw_message: int | str = None) -> types.InlineKeyboardMarkup:
        keyboard = types.InlineKeyboardMarkup()

        if type(throw_message) is int:
            keyboard.add(types.InlineKeyboardButton(text="Меньше", callback_data="<"),
                         types.InlineKeyboardButton(text="Больше", callback_data=">"))


            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_luck_point"), )

        elif throw_message == "GREETING":
            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_luck_point"),
                         types.InlineKeyboardButton(text="Попробовать", callback_data=f"start_game"))

        elif throw_message == "FAILED":
            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_luck_point"),
                         types.InlineKeyboardButton(text="Попробовать", callback_data=f"try_again"))
        elif throw_message == "SUCCESS":
            keyboard.add(types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_luck_point"),
                         types.InlineKeyboardButton(text="Далее", callback_data=f"success"))

        return keyboard


def text_popup(map_file: io.BytesIO, popup_file_name: str, lucker_num=None) -> io.BytesIO:
    map_file = Image.open(map_file)
    popup_file = Image.open(popup_file_name)
    img = map_file.copy()
    img.paste(popup_file, LuckPointConst.POPUP_COORDINATES, mask=popup_file)

    img.convert("RGB")


    if lucker_num:
        draw = ImageDraw.Draw(img)
        fontname = ImageFont.truetype(User.NICKNAME_FONT, 15)
        draw.text((LuckPointConst.how_to_place_lucker_num.get(popup_file_name)), str(lucker_num),
                  font=fontname, fill=(233, 201, 41))

    bytesio = io.BytesIO()

    img.save(bytesio, "PNG", quality=100)

    bytesio.seek(0)

    return bytesio


def dice_spawn(dice: dict, map_file: io.BytesIO, permitted_sum: int) -> (io.BytesIO, int):
    while True:
        a, b = randint(1, 6), randint(1, 6)

        if a + b == permitted_sum:
            continue

        img = Image.open(map_file).copy()
        img.paste(Image.open(dice[a]), (84, 149), mask=Image.open(dice[a]))
        img.paste(Image.open(dice[b]), (210, 149), mask=Image.open(dice[b]))

        bytesio = io.BytesIO()

        img.save(bytesio, "PNG", quality=100)

        bytesio.seek(0)

        return bytesio, a + b


async def interact_with_lucker_handler(call: types.CallbackQuery):
    await LuckPointStages.greeting.set()

    user_hero = create_user_hero(call)

    if randint(0, 999) < 5:
        file = LuckPointConst.PUPSIK_FILE
    else:
        file = LuckPointConst.GREETING_FILE

    photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), file))

    keyboard = LuckPoint.get_keyboard("GREETING")

    await bot.edit_message_media(message_id=call.message.message_id, chat_id=user_hero.user_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(file)

    x, y = LuckPointConst.POPUP_COORDINATES

    user_hero.set_popup(photo.read(), 0, x, y)
    user_hero.set_keyboard(keyboard)


async def pre_first_throw_handler(call: types.CallbackQuery, state: FSMContext):
    await LuckPointStages.first_throw.set()

    lucker_num = randint(3, 11)

    user_hero = create_user_hero(call)

    photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), LuckPointConst.FIRST_THROW_FILE, lucker_num))

    keyboard = LuckPoint.get_keyboard(1)

    async with state.proxy() as container:
        container["throw_num"] = 1
        container["lucker_num"] = lucker_num

    await bot.edit_message_media(message_id=call.message.message_id, chat_id=user_hero.user_id, media=photo,
                                 reply_markup=keyboard)


async def first_throw_handler(call: types.CallbackQuery, state: FSMContext):
    user_predict = call.data

    async with state.proxy() as container:
        lucker_num = container["lucker_num"]

    user_hero = create_user_hero(call)

    photo_in_bytes, dice_sum = dice_spawn(LuckPointConst.dice, get_map(user_hero.user_id), lucker_num)

    photo = InputMediaPhoto(photo_in_bytes)

    await bot.edit_message_media(message_id=call.message.message_id, chat_id=user_hero.user_id, media=photo)

    await asyncio.sleep(3)


    if user_predict == "<" and dice_sum < lucker_num or user_predict == ">" and dice_sum > lucker_num:
        async with state.proxy() as container:
            throw_num = container["throw_num"]

        if throw_num == 3:
            user_hero.add_money(LuckPointConst.PRICE_MONEY)

            photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), LuckPointConst.SUCCESS_FILE))

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo)

            await asyncio.sleep(3)

            await LuckKeepersHouseStates.enter_interior.set()

            photo = InputMediaPhoto(get_map(user_hero.user_id))

            luck_keepers_house = LuckKeepersHouse()

            x, y = user_hero.get_coordinates()

            location_name = user_hero.get_location_name()

            keyboard = luck_keepers_house.get_keyboard(x, y, user_hero.user_id, location_name, is_sitting=0)

            await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                         reply_markup=keyboard)
            return

        else:
            keyboard = LuckPoint.get_keyboard(throw_num)

            luck_point_stages = LuckPointStages()

            await luck_point_stages.set_throw_stage(throw_num)

            lucker_num = randint(3, 11)

            photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id),
                                               LuckPointConst.throw_images_data.get(throw_num + 1), lucker_num))


            async with state.proxy() as container:
                container["throw_num"] = throw_num + 1
                container["lucker_num"] = lucker_num
    else:
        async with state.proxy() as container:
            container["throw_num"] = 1

        keyboard = LuckPoint.get_keyboard("FAILED")

        await LuckPointStages.failed.set()

        photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), LuckPointConst.FAILED_FILE))

    await bot.edit_message_media(message_id=call.message.message_id, chat_id=user_hero.user_id, media=photo,
                                 reply_markup=keyboard)




async def failed_throw_handler(call: types.CallbackQuery, state: FSMContext):
    await LuckPointStages.first_throw.set()

    lucker_num = randint(3, 11)

    async with state.proxy() as container:
        container["lucker_num"] = lucker_num

    user_hero = create_user_hero(call)

    photo = InputMediaPhoto(text_popup(get_map(user_hero.user_id), LuckPointConst.FIRST_THROW_FILE, lucker_num))

    keyboard = LuckPoint.get_keyboard(1)


    await bot.edit_message_media(message_id=call.message.message_id, chat_id=user_hero.user_id, media=photo,
                                 reply_markup=keyboard)


async def exit_from_luck_point_handler(call: types.CallbackQuery):
    await LuckKeepersHouseStates.enter_interior.set()

    user_hero = create_user_hero(call)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    luck_keepers_house = LuckKeepersHouse()

    location_name = user_hero.get_location_name()

    x, y = user_hero.get_coordinates()

    keyboard = luck_keepers_house.get_keyboard(x, y, user_hero.user_id, location_name, is_sitting=0)

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.delete_popup_item()
    user_hero.set_keyboard(keyboard)


def register_luck_point_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(exit_from_luck_point_handler, text="exit_from_luck_point",
                                       state="*")

    dp.register_callback_query_handler(interact_with_lucker_handler, text="interact_with_luck_point",
                                       state=LuckKeepersHouseStates.enter_interior)

    dp.register_callback_query_handler(pre_first_throw_handler, text="start_game", state=LuckPointStages.greeting)

    dp.register_callback_query_handler(first_throw_handler, lambda text: text.data in ("<", ">"),
                                       state=(LuckPointStages.first_throw, LuckPointStages.second_throw,
                                              LuckPointStages.third_throw))

    dp.register_callback_query_handler(failed_throw_handler, text="try_again", state=LuckPointStages.failed)
