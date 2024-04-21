from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from CONSTANTS.POINTS_CONSTANTS import list_with_partial_points_data
from gameLogic.FuncsAndObjects.generals import get_photo_in_bytes, color_data
from gameLogic.logic import Hero
from gameLogic.FuncsAndObjects.narrowly_focused import *
from CONSTANTS.POINTS_CONSTANTS import WardrobeConst

from supportingFiles.connection import bot


class WardrobeStates(StatesGroup):
    enter_wardrobe = State()
    choose_part_of_skin = State()


class Wardrobe:
    @staticmethod
    def get_keyboard_for_choosing_part_of_skin() -> types.InlineKeyboardMarkup:
        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(types.InlineKeyboardButton(text="1. Волосы", callback_data="hair"),
                     types.InlineKeyboardButton(text="2. Кожа", callback_data="skin"),
                     types.InlineKeyboardButton(text="3. Футболка", callback_data="shirt"), )

        keyboard.add(types.InlineKeyboardButton(text="4. Штаны", callback_data="pants"),
                     types.InlineKeyboardButton(text="5. Обувь", callback_data="shoes"), )

        keyboard.add(types.InlineKeyboardButton(text="🚪 Выйти", callback_data="back"))

        return keyboard


async def enter_wardrobe_handler(call: types.CallbackQuery, state: FSMContext):
    await WardrobeStates.enter_wardrobe.set()

    user_hero = create_user_hero(call)

    keyboard = Wardrobe.get_keyboard_for_choosing_part_of_skin()

    photo = get_photo_in_bytes(WardrobeConst.INTERFACE)

    photo = InputMediaPhoto(photo)

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(WardrobeConst.INTERFACE)

    user_hero.set_popup(photo.read(), is_full_screen=1)
    user_hero.set_keyboard(keyboard)



async def exit_wardrobe_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    user_hero = create_user_hero(call)

    keyboard = get_keyboard(user_hero)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.delete_popup_item()
    user_hero.delete_keyboard()


async def choose_part_of_skin_handler(call: types.CallbackQuery, state: FSMContext):
    await WardrobeStates.choose_part_of_skin.set()

    user_hero = create_user_hero(call)

    part_of_skin = call.data

    parts_data = {"hair": WardrobeConst.CHOOSE_HAIR,
                  "skin": WardrobeConst.CHOOSE_SKIN,
                  "shirt": WardrobeConst.CHOOSE_SHIRT,
                  "pants": WardrobeConst.CHOOSE_PANTS,
                  "shoes": WardrobeConst.CHOOSE_SHOES, }

    async with state.proxy() as container:
        container["part_of_skin"] = part_of_skin

    choice = parts_data[part_of_skin]

    photo = InputMediaPhoto(get_photo_in_bytes(choice))

    keyboard = get_keyboard_for_choosing_color()

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(choice)

    user_hero.set_popup(photo.read(), is_full_screen=1)
    user_hero.set_keyboard(keyboard)


async def paint_part_of_skin_handler(call: types.CallbackQuery, state: FSMContext):
    await WardrobeStates.enter_wardrobe.set()

    async with state.proxy() as container:
        part_of_skin = container["part_of_skin"]

    color = call.data

    user_hero = create_user_hero(call)

    user_hero.paint_part_of_skin(part_of_skin, color)

    keyboard = Wardrobe.get_keyboard_for_choosing_part_of_skin()

    photo = InputMediaPhoto(get_photo_in_bytes(WardrobeConst.INTERFACE))


    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(WardrobeConst.INTERFACE)

    user_hero.set_popup(photo.read(), is_full_screen=1)
    user_hero.set_keyboard(keyboard)



async def exit_from_painting_part_of_skin_handler(call: types.CallbackQuery, state: FSMContext):
    await WardrobeStates.enter_wardrobe.set()

    user_hero = create_user_hero(call)

    keyboard = Wardrobe.get_keyboard_for_choosing_part_of_skin()

    photo = InputMediaPhoto(get_photo_in_bytes(WardrobeConst.INTERFACE))

    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    photo = get_photo_in_bytes(WardrobeConst.INTERFACE)

    user_hero.set_popup(photo.read(), is_full_screen=1)
    user_hero.set_keyboard(keyboard)


def register_wardrobe_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(enter_wardrobe_handler, text="enter_wardrobe", state=None)

    dp.register_callback_query_handler(exit_wardrobe_handler, text="back",
                                       state=WardrobeStates.enter_wardrobe)

    dp.register_callback_query_handler(choose_part_of_skin_handler, lambda call: call.data in
                                                                                 ["skin", "hair", "shirt",
                                                                                  "pants", "shoes"],
                                       state=WardrobeStates.enter_wardrobe)

    dp.register_callback_query_handler(paint_part_of_skin_handler,
                                       lambda call: call.data in color_data.keys(),
                                       state=WardrobeStates.choose_part_of_skin)

    dp.register_callback_query_handler(exit_from_painting_part_of_skin_handler, text="back",
                                       state=WardrobeStates.choose_part_of_skin)
