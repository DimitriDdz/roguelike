from aiogram import types, Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.utils.exceptions import Throttled

from ban_logic import get_user_times_exceeded, update_user_times_exceeded, ban_user
from CONSTANTS.POINTS_CONSTANTS import Prison


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit: (float, int) = 0.5):
        super().__init__()
        self.rate_limit = limit

    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        if call.data == "prison_update":
            return

        user_id = call.from_user.id

        # handler = current_handler.get()
        dp = Dispatcher.get_current()

        try:
            await dp.throttle(key="anti-flood_callback", rate=self.rate_limit)
        except Throttled:
            update_user_times_exceeded(call.from_user.id)

            times_exceeded = get_user_times_exceeded(user_id)

            times_exceeded += 1

            if times_exceeded >= Prison.TIMES_EXCEEDED:
                await ban_user(user_id, call)

            raise CancelHandler()
