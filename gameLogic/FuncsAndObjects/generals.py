import io
from datetime import datetime, timedelta
from PIL import Image
from CONSTANTS.USER_CONSTANTS import *
from supportingFiles.connection import cursor, con


color_data = {"red": (176, 35, 35),
              "yellow": (227, 237, 10),
              "orange": (237, 158, 10),
              "green": (10, 109, 18),
              "blue": (13, 24, 73),
              "purple": (176, 35, 240),
              "pink": (224, 154, 154),
              "dark": (57, 46, 31),
              "white": (255, 255, 255),
              "skin": (240, 221, 176),
              "brown": (129, 93, 9),
              "cyan": (38, 164, 173),
              }

side_data = {
    "down": Skin.DEFAULT_DUDE,
    "up": Skin.DEFAULT_DUDE_BACK,
    "left": Skin.DEFAULT_DUDE_LEFT,
    "right": Skin.DEFAULT_DUDE_RIGHT,
}


size_data_if_sitting = {
    "right": Skin.DEFAULT_DUDE_RIGHT_SITTING,
    "left": Skin.DEFAULT_DUDE_LEFT_SITTING,
}


buttons_data_for_encoding = {}


def paint_hero(dude: str, skin_colors: tuple) -> Image:
    skin_color, hair_color, shirt_color, pants_color, shoes_color = skin_colors

    if skin_color == Skin.DEFAULT_SKIN and hair_color == Skin.DEFAULT_HAIR \
            and shirt_color == Skin.DEFAULT_SHIRT and \
            pants_color == Skin.DEFAULT_PANTS and shoes_color == Skin.DEFAULT_SHOES:
        return Image.open(dude)

    im1 = Image.open(dude)
    personal_dude = im1.copy()
    for i in range(30):
        for j in range(40):
            r, g, b, a = personal_dude.getpixel((i, j))
            if a == 0:
                pass
            elif r == 129 and g == 93 and b == 9:
                personal_dude.putpixel((i, j), color_data[hair_color])
            elif r == 240 and g == 221 and b == 176:
                personal_dude.putpixel((i, j), color_data[skin_color])
            elif r == 10 and g == 109 and b == 18:
                personal_dude.putpixel((i, j), color_data[shirt_color])
            elif r == 13 and g == 24 and b == 73:
                personal_dude.putpixel((i, j), color_data[pants_color])
            elif r == 38 and g == 164 and b == 173:
                personal_dude.putpixel((i, j), color_data[shoes_color])

    return personal_dude


def get_photo_in_bytes(name: str) -> io.BytesIO:
    photo = Image.open(name)

    bytesio = io.BytesIO()

    photo.save(bytesio, format="PNG")

    bytesio.seek(0)

    return bytesio


def get_time_in_right_format() -> str:
    """Получение времени в формате YY/MM/DD HH:MM:SS"""

    time_ = str(datetime.utcnow())

    date = time_.split()[0]

    time_ = time_.split()[1].split(".")[0]

    last_action_time = date + " " + time_

    return last_action_time


def update_position(user_id: int, is_sitting: int) -> None:
    cursor.execute("UPDATE users_coordinates SET is_sitting = ? WHERE user_id = ?", (is_sitting, user_id, ))
    con.commit()


def is_banned(user_id: int) -> bool:
    ban_time = cursor.execute("SELECT ban_time FROM users_ban WHERE user_id =?", (user_id,)).fetchone()[0]

    if not ban_time:
        return True

    datetime_object = datetime.strptime(ban_time, "%Y-%m-%d %H:%M:%S")

    if datetime_object.utcnow() - timedelta(seconds=User.BAN_TIME_IN_SECONDS) >= datetime_object:
        return True

    return False


def get_username(user_id: int) -> str:
    username = cursor.execute("SELECT username FROM users WHERE id == ?", (user_id,)).fetchone()[0]

    return username


def text_popup(map_file: io.BytesIO, popup_file: io.BytesIO, x, y) -> io.BytesIO:
    map_file = Image.open(map_file)
    popup_file = Image.open(popup_file)
    img = map_file.copy()
    img.paste(popup_file, (x, y), mask=popup_file)

    img.convert("RGB")

    bytesio = io.BytesIO()

    img.save(bytesio, "PNG", quality=100)

    bytesio.seek(0)

    return bytesio
