from aiogram import Dispatcher, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from gameLogic.FuncsAndObjects.narrowly_focused import *
from supportingFiles.connection import bot
from CONSTANTS.POINTS_CONSTANTS import LuckKeepersHouseConst, SpawnPoint
from CONSTANTS.USER_CONSTANTS import User


class LuckKeepersHouseStates(StatesGroup):
    enter_interior = State()


class LuckKeepersHouse:
    BUTTON = types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_luck_keepers_house")

    LUCK_POINT_COORDINATES = (220, 115)
    LUCK_POINT_BUTTON = types.InlineKeyboardButton(text="Взаимодействовать",
                                                   callback_data="interact_with_luck_point")

    EXIT_BUTTON = types.InlineKeyboardButton(text="Выйти", callback_data="exit_from_luck_keepers_house")

    STAND_UP_BUTTON = types.InlineKeyboardButton(text="Встать", callback_data="stand_up")

    CHAIRS_COORDINATES = {(140, 165): types.InlineKeyboardButton(text="Сесть",
                                                                 callback_data="sit_at: 140, 165; left"),
                          (55, 165): types.InlineKeyboardButton(text="Сесть",
                                                                callback_data="sit_at: 55, 165; right"),
                          (140, 245): types.InlineKeyboardButton(text="Сесть",
                                                                 callback_data="sit_at: 140, 245; left"),
                          (55, 245): types.InlineKeyboardButton(text="Сесть",
                                                                callback_data="sit_at: 55, 245; right")}

    def get_keyboard(self, x: int, y: int, location_name: str, self_id: int, is_sitting: int | bool = 0) -> \
            types.InlineKeyboardMarkup:

        keyboard = types.InlineKeyboardMarkup()

        if is_sitting:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬆', callback_data='#'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))
        else:
            keyboard.add(types.InlineKeyboardButton(text='�', callback_data='None'),
                         types.InlineKeyboardButton(text='⬆', callback_data='up'),
                         types.InlineKeyboardButton(text='�', callback_data='None'))

        step = User.STEP_IN_PIXELS

        luck_point_x, luck_point_y = self.LUCK_POINT_COORDINATES

        if 0 <= abs(luck_point_x - x) <= step + 1 and 0 <= abs(luck_point_y - y) <= step + 1:
            button_ = self.LUCK_POINT_BUTTON
        elif 0 <= abs(LuckKeepersHouseConst.DEFAULT_X - x) <= step + 1 and 0 <= abs(LuckKeepersHouseConst.DEFAULT_Y - y) <= step + 1:
            button_ = self.EXIT_BUTTON
        else:
            for coordinates, chair_button in self.CHAIRS_COORDINATES.items():
                x_, y_ = coordinates
                if abs(x_ - x) <= step and abs(y_ - y) <= step:
                    if not is_sitting:
                        if check_coordinates(x_, y_, self_id, location_name):
                            button_ = chair_button
                        else:
                            button_ = None
                    else:
                        button_ = self.STAND_UP_BUTTON
                    break
            else:
                button_ = None

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


# text="enter_luck_keepers_house", state=None
async def enter_luck_keepers_house_handler(call: types.CallbackQuery):
    await LuckKeepersHouseStates.enter_interior.set()

    user_hero = create_user_hero(call)

    user_hero.update_location(LuckKeepersHouseConst.NAME)


    user_hero.update_coordinates(LuckKeepersHouseConst.DEFAULT_X, LuckKeepersHouseConst.DEFAULT_Y, LuckKeepersHouseConst.DEFAULT_SIDE)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    luck_keepers_house = LuckKeepersHouse()

    x, y = user_hero.get_coordinates()

    location_name = user_hero.get_location_name()

    keyboard = luck_keepers_house.get_keyboard(x, y, location_name, user_hero.user_id)

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.set_keyboard(keyboard)


async def move_in_luck_keepers_house_handler(call: types.CallbackQuery):
    user_hero = create_user_hero(call)

    user_hero.update_position(0)

    side = call.data

    x, y = user_hero.get_coordinates()

    user_hero.update_coordinates(x, y, side)

    luck_keepers_house = LuckKeepersHouse()

    location_name = user_hero.get_location_name()

    x, y = user_hero.get_coordinates()

    keyboard = luck_keepers_house.get_keyboard(x, y, location_name, user_hero.user_id)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    try:
        await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                     reply_markup=keyboard)
    except (exceptions.MessageNotModified, exceptions.BadRequest) as e:
        print(e)

    user_hero.set_keyboard(keyboard)


async def exit_from_luck_keepers_house_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    user_hero = create_user_hero(call)

    user_hero.update_location(SpawnPoint.NAME)

    user_hero.update_coordinates(LuckKeepersHouseConst.X, LuckKeepersHouseConst.Y, "down")

    keyboard = get_keyboard(user_hero)

    photo = InputMediaPhoto(get_map(call.from_user.id))

    user_hero.set_keyboard(keyboard)
    user_hero.delete_popup_item()

    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)


async def sit_at_handler(call: types.CallbackQuery):
    coordinates_string, side = call.data.replace("sit_at: ", "").split("; ")

    coordinates = [int(i) for i in coordinates_string.split(", ")]

    x, y = coordinates

    user_hero = create_user_hero(call)

    user_hero.update_position(1)

    user_hero.update_coordinates(*coordinates, side, check=False)

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    luck_keepers_house = LuckKeepersHouse()

    location_name = user_hero.get_location_name()

    keyboard = luck_keepers_house.get_keyboard(x, y, location_name, user_hero.user_id, is_sitting=1)

    await bot.edit_message_media(chat_id=user_hero.user_id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.set_keyboard(keyboard)


async def stand_up_handler(call: types.CallbackQuery):
    user_hero = create_user_hero(call)

    user_hero.update_position(0)

    x, y = user_hero.get_coordinates()

    photo = InputMediaPhoto(get_map(user_hero.user_id))

    luck_keepers_house = LuckKeepersHouse()

    location_name = user_hero.get_location_name()

    keyboard = luck_keepers_house.get_keyboard(x, y, location_name, user_hero.user_id)

    await bot.edit_message_media(chat_id=call.from_user.id, message_id=call.message.message_id, media=photo,
                                 reply_markup=keyboard)

    user_hero.set_keyboard(keyboard)


def register_luck_keepers_house_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(enter_luck_keepers_house_handler, text="enter_luck_keepers_house", state=None)
    dp.register_callback_query_handler(move_in_luck_keepers_house_handler,
                                       lambda call: call.data in ["up", "down", "left", "right"],
                                       state=LuckKeepersHouseStates.enter_interior)
    dp.register_callback_query_handler(exit_from_luck_keepers_house_handler, text="exit_from_luck_keepers_house",
                                       state=LuckKeepersHouseStates.enter_interior)
    dp.register_callback_query_handler(sit_at_handler, text_contains="sit_at",
                                       state=LuckKeepersHouseStates.enter_interior)
    dp.register_callback_query_handler(stand_up_handler, text="stand_up", state=LuckKeepersHouseStates.enter_interior)
