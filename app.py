import asyncio

from aiogram import Dispatcher

from dotenv import find_dotenv, load_dotenv

from bot_instance import bot

load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, session_maker

from handlers.user.user_private import user_private_router
from handlers.group.user_group import user_group_router
from handlers.admin.admin_private import admin_router


# bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# bot.my_admins_list = []


dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup(bot):
    # await drop_db()

    await create_db()


async def main():
    dp.startup.register(on_startup)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
