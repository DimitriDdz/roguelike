from PIL import Image
from aiogram import types


class Prison:
    PRISON_FILE = "images/map/prison.png"
    TIMES_EXCEEDED = 10

    RATE_LIMIT_IN_SECONDS = 0.3


class Items:
    COIN_IMAGE = "images/item_icons/coin.png"


class SpawnPoint:
    NAME = "spawn"

    SPAWN_FILE = "images/map/spawn_location.png"

    SPAWN_FILE_X = Image.open(SPAWN_FILE).size[0]
    SPAWN_FILE_Y = Image.open(SPAWN_FILE).size[1]

    DEFAULT_X = 450
    DEFAULT_Y = 110

    PERMITTED_COORDINATES = [
        #  LEFT_DOWN, RIGHT_UP
        [(0, 310), (1440, 170)],
        [(0, 110), (580, -30)],
        [(640, 110), (1900, 0)],
        [(1480, 290), (1900, 170)],
        [(640, 20), (700, -20)],
        # Temporarily
        [(500, 0), (650, -40)],
        [(1880, 300), (2000, 0)],
        [(1400, 350), (1550, 290)]
    ]


class WardrobeConst:
    INTERFACE = "images/map/wardrobe/interface.png"
    CHOOSE_HAIR = "images/map/wardrobe/hair_colors.png"
    CHOOSE_SKIN = "images/map/wardrobe/skin_colors.png"
    CHOOSE_SHIRT = "images/map/wardrobe/shirt_colors.png"
    CHOOSE_PANTS = "images/map/wardrobe/pants_colors.png"
    CHOOSE_SHOES = "images/map/wardrobe/shoes_colors.png"

    BUTTON = types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_wardrobe")

    BUTTONS = (BUTTON,
               types.InlineKeyboardButton(text="1. Волосы", callback_data="hair"),
               types.InlineKeyboardButton(text="2. Кожа", callback_data="skin"),
               types.InlineKeyboardButton(text="3. Футболка", callback_data="shirt"),
               types.InlineKeyboardButton(text="4. Штаны", callback_data="pants"),
               types.InlineKeyboardButton(text="5. Обувь", callback_data="shoes"),

               )

    X = 450
    Y = 110


class LuckKeepersHouseConst:
    SPAWN_FILE = "images/map/luck_keepers_house/interior.png"

    NAME = "luck_keepers_house"

    X = 760
    Y = 110

    DEFAULT_X = 200
    DEFAULT_Y = 315
    DEFAULT_SIDE = "up"

    # -20, 315

    PERMITTED_COORDINATES = [
        #  LEFT_DOWN, RIGHT_UP
        [(105, 115), (320, 15)],
        [(-20, 335), (180, 295)],
        [(-40, 315), (15, 15)],
        [(0, 35), (500, -40)],
        [(340, 335), (500, -40)],
        [(-20, 335), (380, 295)],
        [(65, 185), (135, 130)],
        [(65, 265), (135, 210)]
    ]


class LuckPointConst:
    GREETING_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/greetings.png"
    GOODBYE_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/goodbye.png"

    FAILED_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/failed.png"
    SUCCESS_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/success.png"

    PUPSIK_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/pupsik.png"

    FIRST_THROW_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/first_throw.png"
    SECOND_THROW_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/second_throw.png"
    THIRD_THROW_FILE = "images/map/luck_keepers_house/luck_point/throws_and_service/third_throw.png"

    PRICE_MONEY = 100

    dice = {
        1: "images/map/luck_keepers_house/luck_point/dice/dice1.png",
        2: "images/map/luck_keepers_house/luck_point/dice/dice2.png",
        3: "images/map/luck_keepers_house/luck_point/dice/dice3.png",
        4: "images/map/luck_keepers_house/luck_point/dice/dice4.png",
        5: "images/map/luck_keepers_house/luck_point/dice/dice5.png",
        6: "images/map/luck_keepers_house/luck_point/dice/dice6.png"
    }

    throw_images_data = {
        1: FIRST_THROW_FILE,
        2: SECOND_THROW_FILE,
        3: THIRD_THROW_FILE,
    }

    how_to_place_lucker_num = {
        FIRST_THROW_FILE: (192, 254),
        SECOND_THROW_FILE: (232, 271),
        THIRD_THROW_FILE: (250, 254),
    }

    POPUP_COORDINATES = (2, 230)



class DrugstoreConst:
    X = 885
    Y = 110

    NAME = "drugstore"

    DRUG = "images/map/drugstore/drug.png"

    GREETING_FILE = "images/map/drugstore/greeting.png"
    TASK_FILE = "images/map/drugstore/task.png"
    SUCCESS_FILE = "images/map/drugstore/success.png"
    FAILURE_FILE = "images/map/drugstore/failure.png"

    ITEM_POPUP = "images/map/drugstore/item_popup.png"

    AVERAGE_POPUP_COORDINATES = (2, 230)
    ITEM_POPUP_COORDINATES = (243, 279)


class QuizConst:
    SPAWN_FILE = "images/map/quiz/interior.png"

    WAITING_FOR_OTHER_PLAYER_FILE = ""

    NAME = "quiz"

    X = 1000
    Y = 110

    DEFAULT_X = 195
    DEFAULT_Y = 320

    PERMITTED_COORDINATES = [
        [(180, 400), (1000, 300)],
        [(345, 400), (1000, 0)],
        [(0, 20), (1000, -40)],
        [(-20, 320), (15, 20)],
        [(20, 80), (180, 0)],
        [(190, 80), (340, 0)]
    ]

    DEFAULT_SIDE = "up"



locations_name_data = {
    SpawnPoint.NAME: SpawnPoint,
    LuckKeepersHouseConst.NAME: LuckKeepersHouseConst,
    QuizConst.NAME: QuizConst,
}

NOT_ZOOM_LOCATIONS = [LuckKeepersHouseConst, QuizConst]

LOCATIONS_NAMES_THAT_USE_STAGES = [LuckKeepersHouseConst.NAME]

TASKS_ITEMS_FILES = {DrugstoreConst.NAME: DrugstoreConst.DRUG}

list_with_partial_points_data = [
    # Wardrobe
    [types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_wardrobe"), (WardrobeConst.X, WardrobeConst.Y)],
    # Luck_Keepers_House
    [types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_luck_keepers_house"),
     (LuckKeepersHouseConst.X, LuckKeepersHouseConst.Y)],
    # Drugstore
    [types.InlineKeyboardButton(text="Взаимодействовать", callback_data="to_interact_with_drugstore"),
     (DrugstoreConst.X, DrugstoreConst.Y)],
    # Quiz
    [types.InlineKeyboardButton(text="🚪 Войти", callback_data="enter_quiz"), (QuizConst.X, QuizConst.Y)]
]

items_tasks_data = {"drugstore": types.InlineKeyboardButton(text="Взять",
                                                            callback_data="get_drugstore_item")}

CANT_USE_START_STATES = ("LuckPointStages:first_throw",
                         "LuckPointStages:second_throw",
                         "LuckPointStages:third_throw",
                         "LuckPointStages:failed", )

