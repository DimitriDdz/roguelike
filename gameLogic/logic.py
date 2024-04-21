import asyncio
import io

from gameLogic.FuncsAndObjects.generals import *
from CONSTANTS.USER_CONSTANTS import *
from CONSTANTS.POINTS_CONSTANTS import *
from supportingFiles.connection import con, cursor
from PIL import ImageDraw, ImageFont
from weather import get_weather, weather_images_dict

import pickle
from aiogram import types

from CONSTANTS.POINTS_CONSTANTS import items_tasks_data


class HeroException(Exception):
    pass


class Hero:
    def __init__(self, user_id: int, update_last_action_time=True) -> None:
        self.user_id = user_id
        self.username = get_username(user_id)

        # Так как юзернейм пользователя изменяем, при каждом движении персонажа юзернейм обновляется
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (self.username, user_id,))
        con.commit()

        # Получение изображения пользователя, основываясь на том, в какую сторону смотрит персонаж
        side = cursor.execute("SELECT side FROM users_coordinates WHERE user_id == ?", (user_id,)).fetchone()[0]

        if side:
            is_sitting = cursor.execute("SELECT is_sitting FROM users_coordinates WHERE user_id == ?",
                                        (self.user_id,)).fetchone()[0]

            if is_sitting:
                dude_image = size_data_if_sitting.get(side)
            else:
                dude_image = side_data.get(side)

            if not dude_image:
                raise HeroException("Invalid side: must be 'up', 'down', 'left' or 'right'")

        else:
            dude_image = Skin.DEFAULT_DUDE

        # Получение цвета каждой части тела
        skin_colors = self.get_skin_colors()

        self.dude_image = paint_hero(dude_image, skin_colors)

        if update_last_action_time:
            self.update_last_action_time()

    def get_message_id(self) -> int:
        """Возвращает id последнего сообщения, отправленного ботом"""

        message_id = cursor.execute("SELECT message_id FROM users WHERE id == ?", (self.user_id,)).fetchone()[0]

        return message_id

    def set_message_id(self, message_id: int):
        """Обновляет id последнего сообщения, отправленного ботом"""

        cursor.execute("UPDATE users SET message_id == ? WHERE id = ?", (message_id, self.user_id))
        con.commit()

    def spawn_nickname(self, location: Image, fontname: str, x: int, y: int) -> Image:
        """Размещает никнейм игрока над ним"""

        display_name = self.get_username()

        # location - ПОЛНАЯ КАРТА, а не зазумленная, ибо тогда коориданты ломаются
        img = location.copy()
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(fontname, 17)

        d, _, w, _ = draw.textbbox((x, y - 18), display_name, font=font)
        draw.text((x + 15 - ((w - d) / 2), y - 18), display_name, font=font)

        return img

    def zoom_to_player(self, map_file: Image, x: int) -> io.BytesIO:
        """Фокусирует изображение на пользователе"""

        money = self.get_money()

        if self.get_location() in NOT_ZOOM_LOCATIONS:
            coin = Image.open(Items.COIN_IMAGE)
            map_file.paste(coin, (5, 5), mask=coin)
            font = ImageFont.truetype(User.NICKNAME_FONT, 14)
            draw = ImageDraw.Draw(map_file)
            draw.text((23, 5), str(money), font=font)

            bytesio = io.BytesIO()

            map_file.save(bytesio, format="PNG", quality=100)

            bytesio.seek(0)

            return bytesio

        k = 0
        w, h = map_file.size
        img = map_file.crop(((x - w // 10), 0, (x + w // 10), 351))
        if x < 600:
            r, g, b = img.getpixel((0, 0))
            while r == 0 and g == 0 and b == 0:
                k += 1
                img = map_file.crop(((x - w // 10) + k, 0, (x + w // 10) + k, 351))
                r, g, b = img.getpixel((0, 0))
        if x > 1500:
            r, g, b = img.getpixel((383, 350))
            while r == 0 and g == 0 and b == 0:
                k -= 1
                img = map_file.crop(((x - w // 10) + k, 0, (x + w // 10) + k, 351))
                r, g, b = img.getpixel((383, 350))

        if self.should_update_weather():
            city = self.get_city()
            image_path, weather = get_weather(city)
            self.set_weather(weather)
            self.set_last_weather_update_time()
        else:
            weather = self.get_weather()
            image_path = weather_images_dict.get(weather)
            if not image_path:
                city = self.get_city()
                image_path, weather = get_weather(city)
            self.set_weather(weather)

        weather_filter = Image.open(image_path)  # ну сюда файлы короч которые я тебе скину
        img.paste(weather_filter, (0, 0), mask=weather_filter)
        coin = Image.open(Items.COIN_IMAGE)
        img.paste(coin, (5, 5), mask=coin)
        font = ImageFont.truetype(User.NICKNAME_FONT, 14)
        draw = ImageDraw.Draw(img)
        draw.text((23, 5), str(money), font=font)

        bytesio = io.BytesIO()

        img.save(bytesio, format="PNG", quality=100)

        bytesio.seek(0)

        return bytesio

    def set_popup(self, popup_in_bytes: bytes, is_full_screen: bool, x: int = 0, y: int = 0,
                  delete_next_time: int = 0) -> None:
        cursor.execute("UPDATE users_popup SET photo_in_bytes == ?, is_full_screen == "
                       "?, x == ?, y == ?, delete_next_time == ? WHERE user_id == ?", (popup_in_bytes, is_full_screen,

                                                                                       x, y, delete_next_time,
                                                                                       self.user_id))
        con.commit()

    def get_popup(self) -> io.BytesIO or None:
        popup, is_full_screen, x, y, delete_next_time = cursor.execute("SELECT photo_in_bytes, is_full_screen, "
                                                                       "x, y, delete_next_time FROM users_popup WHERE "
                                                                       "user_id = ?",
                                                                       (self.user_id,)).fetchone()
        if popup:
            bytesio = io.BytesIO()
            img = Image.open(io.BytesIO(popup))

            img.save(bytesio, format="PNG", quality=100)

            bytesio.seek(0)

            print(is_full_screen)

            return bytesio, is_full_screen, x, y, delete_next_time

    def delete_popup_item(self) -> None:
        cursor.execute("UPDATE users_popup SET photo_in_bytes == ? WHERE user_id == ?", (None, self.user_id,))
        con.commit()

    def get_state_name(self):
        """Возвращает имя состояния"""

        state = cursor.execute("SELECT state FROM aiogram_state WHERE user == ?", (self.user_id,)).fetchone()

        if state:
            return state[0]

    def spawn(self, x: int, y: int, location: Image = None) -> Image:
        """Размещает персонажа на карте"""

        if not location:
            location = self.get_location()

            spawn_file = Image.open(location.SPAWN_FILE)
        else:
            spawn_file = location

        im1 = spawn_file
        im2 = self.dude_image
        final = im1.copy()

        final.paste(im2, (x, y), mask=im2)

        final.convert("RGB")

        # if self.user_id == my_id:
        #     final.show()

        return final

    def spawn_task_item(self, spawn_file: Image) -> Image:
        """Размещает особый предмет на карте, видимый только для пользователя"""

        task_name = self.get_task_name()

        if task_name:
            is_received = self.task_is_received(task_name)

            if not is_received:
                drug = Image.open(TASKS_ITEMS_FILES.get(task_name))

                drug_coordinates = self.get_task_item_coordinates(task_name)

                spawn_file = spawn_file.copy()

                spawn_file.paste(drug, drug_coordinates, mask=drug)

        return spawn_file

    def paint_part_of_skin(self, part_of_skin: str, color: str) -> None:
        """Обновляет цвет части тела персонажа"""

        cursor.execute(f"UPDATE users_skins SET {part_of_skin} = ? WHERE user_id = ?", (color, self.user_id,))
        con.commit()

    def update_last_action_time(self) -> None:
        """Обновляет время последней активности пользователя"""

        new_time = get_time_in_right_format()

        cursor.execute("UPDATE users_time SET last_action_time =? WHERE user_id = ?", (new_time, self.user_id))
        con.commit()

    def get_last_action_time(self) -> datetime:
        """Возвращает время последней активности пользователя"""

        last_action_time = cursor.execute("SELECT last_action_time FROM users_time WHERE user_id == ?",
                                          (self.user_id,)).fetchone()[0]

        datetime_object = datetime.strptime(last_action_time, "%Y-%m-%d %H:%M:%S")

        return datetime_object

    def check_time(self) -> bool:
        """Проверка на то, бездействовал ли пользователь больше определённого времени"""

        last_action_time = cursor.execute("SELECT last_action_time FROM users_time WHERE user_id = ?",
                                          (self.user_id,)).fetchone()[0]

        datetime_object = datetime.strptime(last_action_time, "%Y-%m-%d %H:%M:%S")

        if datetime_object + timedelta(minutes=10) <= datetime.utcnow():
            return False

        return True

    def get_coordinates(self) -> tuple:
        """Получение координат персонажа"""

        current_coordinates = cursor.execute("SELECT x, y FROM users_coordinates WHERE user_id =?",
                                             (self.user_id,)).fetchone()

        return current_coordinates

    def update_coordinates(self, x: int, y: int, side: str, check: bool = True) -> None:
        """Обновление координат персонажа"""

        if check:
            res = self.check_ability_to_move(x, y, side)
        else:
            res = (x, y)
        if res:
            cursor.execute("UPDATE users_coordinates SET x = ?, y = ?, side = ? WHERE user_id =?",
                           (*res, side, self.user_id))
            con.commit()
        else:
            cursor.execute("UPDATE users_coordinates SET side = ? WHERE user_id =?",
                           (side, self.user_id))
            con.commit()

    def get_skin_colors(self) -> tuple:
        """Получение цвета каждой части тела"""

        skin_colors = cursor.execute("SELECT skin, hair, shirt, pants, shoes FROM users_skins WHERE user_id =?",
                                     (self.user_id,)).fetchone()

        return skin_colors

    def get_username(self) -> str:
        """Возвращает никнейм персонажа"""

        username = cursor.execute("SELECT username FROM users WHERE id == ?", (self.user_id,)).fetchone()[0]

        return username

    def get_location_name(self) -> str:
        """Возвращает имя локации, на которой находится пользователь"""

        location_name = cursor.execute("SELECT location_name FROM users_coordinates WHERE user_id = ?",
                                       (self.user_id,)).fetchone()[0]

        return location_name

    def get_location(self):
        location_name = self.get_location_name()

        return locations_name_data.get(location_name.strip())

    def get_task_location(self):
        """Возвращает класс, содержащий данные о локации"""

        if self.get_task_name():
            task_location_name = \
                cursor.execute("SELECT location_name FROM users_task WHERE user_id = ?", (self.user_id,)).fetchone()[0]

            return locations_name_data.get(task_location_name.strip())

    def update_location(self, location_name) -> None:
        """Обновляет имя локации"""

        cursor.execute("UPDATE users_coordinates SET location_name = ? WHERE user_id = ?",
                       (location_name, self.user_id))
        con.commit()

    def check_ability_to_move(self, x: int, y: int, side: str) -> bool | tuple:
        """Проверяет на то, может ли пользователь двигаться в определённом направлении"""

        location = self.get_location()

        step = User.STEP_IN_PIXELS

        data_for_movements = {"up": -step, "down": step, "left": -step, "right": step}

        new_x, new_y = x, y

        if side in ["up", "down"]:
            new_y = y + data_for_movements.get(side)
        else:
            new_x = x + data_for_movements.get(side)

        if not location.PERMITTED_COORDINATES:
            return new_x, new_y

        for coordinates in location.PERMITTED_COORDINATES:
            x_min, y_max = coordinates[0]
            x_max, y_min = coordinates[1]

            if (x_min < new_x < x_max) and (y_min < new_y < y_max):
                if side in ["up", "down"]:
                    if y > y_max:
                        new_y = y_max
                        return new_x, new_y
                    elif y < y_min:
                        new_y = y_min
                        return new_x, new_y
                else:
                    if x > x_max:
                        new_x = x_max
                        return new_x, new_y
                    elif x < x_min:
                        new_x = x_min
                        return new_x, new_y

                return False

        return new_x, new_y

    def get_money(self) -> int:
        """Возвращает количество финансов пользователя"""

        money = cursor.execute("SELECT money FROM users_money WHERE user_id == ?", (self.user_id,)).fetchone()[0]

        return money

    def add_money(self, value: int) -> None:
        """Добавляет некоторое количество финансов к имеющимся финансам"""

        cursor.execute("UPDATE users_money SET money = ? WHERE user_id = ?", (self.get_money() + value, self.user_id,))
        con.commit()

    def get_task_time(self, task_name: str) -> datetime | None:
        """Возвращает время, в которое было взято задание"""

        task_time = cursor.execute(f"SELECT task_time FROM {task_name}_task WHERE user_id = ?",
                                   (self.user_id,)).fetchone()

        if not task_time:
            return

        datetime_object = datetime.strptime(task_time[0], "%Y-%m-%d %H:%M:%S")

        return datetime_object

    def get_task_item_coordinates(self, task_name: str) -> (int, int):
        """Возвращает координаты особого предмета"""

        x, y = cursor.execute(f"SELECT item_x, item_y FROM {task_name}_task WHERE user_id = ?",
                              (self.user_id,)).fetchone()

        return x, y

    def set_task(self, task_name: str, task_time: str, location_name: str, x: int, y: int) -> None:
        """Устанавливает задание, которое взял пользователь"""

        cursor.execute(f"INSERT INTO {task_name}_task (user_id, task_time, item_x, item_y, is_received) VALUES (?, ?, "
                       f"?, ?, ?)",
                       (self.user_id, task_time, x, y, 0))
        con.commit()

        cursor.execute("INSERT INTO users_task (user_id, task_name, location_name) VALUES (?, ?, ?)",
                       (self.user_id, task_name, location_name))
        con.commit()

    def receive_item_task(self, task_name: str) -> None:
        cursor.execute(f"UPDATE {task_name}_task SET is_received = ? WHERE user_id = ?", (1, self.user_id))
        con.commit()

    def delete_task(self, task_name: str) -> None:
        """Удаляет задание пользователя"""

        cursor.execute(f"DELETE FROM {task_name}_task WHERE user_id = ?", (self.user_id,))
        con.commit()

        cursor.execute(f"DELETE FROM users_task WHERE user_id = ?", (self.user_id,))
        con.commit()

    def task_is_received(self, task_name: str) -> bool:
        is_received = cursor.execute(f"SELECT is_received FROM {task_name}_task WHERE user_id = ?",
                                     (self.user_id,)).fetchone()[0]

        return bool(is_received)

    def get_task_name(self) -> str or None:
        """Возвращает имя задания"""

        task_name = cursor.execute("SELECT task_name FROM users_task WHERE user_id = ?", (self.user_id,)).fetchone()

        if not task_name:
            return None

        return task_name[0]

    def get_city(self) -> str or None:
        city = cursor.execute("SELECT city FROM users_weather WHERE user_id == ?", (self.user_id, )).fetchone()[0]
        print(city)
        return city

    def get_weather(self):
        weather = cursor.execute("SELECT weather from users_weather WHERE user_id == ?", (self.user_id, )).fetchone()[0]
        return weather

    def set_weather(self, weather):
        cursor.execute("UPDATE users_weather SET weather = ? WHERE user_id == ?", (weather, self.user_id))
        con.commit()

    def set_city(self, city):
        cursor.execute("UPDATE users_weather SET city = ? WHERE user_id == ?", (city, self.user_id))
        con.commit()

    def update_position(self, is_sitting: int) -> None:
        """Обновляет положение пользователя (сидит - 0, стоит - 1)"""

        cursor.execute("UPDATE users_coordinates SET is_sitting = ? WHERE user_id = ?", (is_sitting, self.user_id,))
        con.commit()

    def set_state(self, state_name: str) -> None:
        """Устанавливает состояние пользователя"""

        cursor.execute("UPDATE aiogram_state SET state = ? WHERE user = ?", (state_name, self.user_id))
        con.commit()


    def set_keyboard(self, keyboard):
        """Устанавливает кнопки, отправленные ботом"""

        pdata = pickle.dumps(keyboard, pickle.HIGHEST_PROTOCOL)

        cursor.execute("UPDATE users_popup SET keyboard == ? WHERE user_id == ?", (pdata, self.user_id))
        con.commit()

    def get_keyboard(self) -> types.InlineKeyboardMarkup or None:
        """Возвращает кнопки, отправленные ботом"""

        keyboard = cursor.execute("SELECT keyboard FROM users_popup WHERE user_id == ?", (self.user_id,)).fetchone()[0]

        if not keyboard:
            return

        keyboard = pickle.loads(keyboard)

        return keyboard

    def delete_keyboard(self):
        """Удаляет из бд кнопки, отправленные ботом"""

        cursor.execute("UPDATE users_popup SET keyboard == ? WHERE user_id == ?", (None, self.user_id))
        con.commit()

    def should_update_weather(self):
        last_weather_update_time = self.get_last_weather_update_time()
        return datetime.utcnow() - timedelta(minutes=1) >= last_weather_update_time

    def set_last_weather_update_time(self):
        last_weather_update_time = get_time_in_right_format()

        cursor.execute("UPDATE users_weather SET last_update_time = ? WHERE user_id = ?", (last_weather_update_time, self.user_id))
        con.commit()

    def get_last_weather_update_time(self):
        last_weather_update_time = cursor.execute("SELECT last_update_time FROM users_weather WHERE user_id = ?", (self.user_id, )).fetchone()[0]
        datetime_object = datetime.strptime(last_weather_update_time, "%Y-%m-%d %H:%M:%S")
        return datetime_object


class RegisterHero(Hero):
    def __init__(self, user_id: int, username: str) -> None:
        if not username:
            username = User.DEFAULT_NICKNAME

        self.user_id = user_id
        self.dude_image = Skin.DEFAULT_DUDE
        self.username = username

    def register_user(self) -> None:
        """Добавление пользователя в базу данных"""

        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (self.user_id, self.username,))
        con.commit()

        self.set_default_skin()
        self.set_default_coordinates()
        self.set_last_action_time()
        self.set_ban_data()
        self.set_start_money()
        self.set_empty_popup()
        self.set_default_city()
        self.set_last_weather_update_time()

    def set_default_skin(self) -> None:
        """Добавление базового скина персонажа"""

        cursor.execute("INSERT INTO users_skins (skin, hair, shirt, pants, shoes, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (
                           Skin.DEFAULT_SKIN, Skin.DEFAULT_HAIR, Skin.DEFAULT_SHIRT, Skin.DEFAULT_PANTS,
                           Skin.DEFAULT_SHOES,
                           self.user_id,))
        con.commit()

    def set_default_coordinates(self) -> None:
        """Добавление координат спавна персонажу"""

        cursor.execute("INSERT INTO users_coordinates (x, y, location_name, user_id) VALUES (?, ?, ?, ?)",
                       (SpawnPoint.DEFAULT_X, SpawnPoint.DEFAULT_Y, "spawn", self.user_id,))
        con.commit()

    def set_last_action_time(self) -> None:
        """Добавление времени последнего действия пользователя"""

        last_action_time = get_time_in_right_format()

        cursor.execute("INSERT INTO users_time (last_action_time, user_id) VALUES (?, ?)",
                       (last_action_time, self.user_id))
        con.commit()

    def set_ban_data(self) -> None:
        cursor.execute("INSERT INTO users_ban (ban_time, times_exceeded, user_id) VALUES (?, ?, ?)",
                       ("", 0, self.user_id,))
        con.commit()

    def set_start_money(self) -> None:
        cursor.execute("INSERT INTO users_money (money, user_id) VALUES (?, ?)", (User.START_MONEY, self.user_id))
        con.commit()

    def set_empty_popup(self) -> None:
        cursor.execute("INSERT INTO users_popup (photo_in_bytes, user_id) VALUES(?, ?)", ("", self.user_id))
        con.commit()

    def set_default_city(self) -> None:
        cursor.execute("INSERT INTO users_weather (city, user_id) VALUES (?, ?)", ("Москва", self.user_id))
        con.commit()
