import os
import asyncio
import logging

from aiogram.types import ParseMode
from aiogram import Bot, Dispatcher
from colorama import Fore, Back, Style, init
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.redis import RedisStorage2, RedisStorage
from aiogram.contrib.middlewares.environment import EnvironmentMiddleware

# FILES <
from config import *
from utils.broadcast import *
from misc.set_bot_commands import *
from models.database import *
from middlewares.acl import *
from middlewares.user_update import *

from handlers.user import *
from handlers.admin import *
from handlers.errors import *
# FILES >

logger = logging.getLogger(__name__)

async def printt():
	print(Fore.GREEN + """
	████  ████ ███    █   █ ███ █  █ ███    ████ █  █ █   ███ █  █ ███
	█  ██ █  █  █     █   █ █   ██ █  █     █  █ ██ █ █    █  ██ █ █  
	████  █  █  █     █ █ █ ███ █ ██  █     █  █ █ ██ █    █  █ ██ ███
	█  ██ █  █  █     █████ █   █  █  █     █  █ █  █ █    █  █  █ █  
	████  ████  █      █ █  ███ █  █  █     ████ █  █ ███ ███ █  █ ███
""" + Style.RESET_ALL)

async def main():
	if SETTINGS['debug_mode']:
		if os.name == "nt":
			os.system("cls")
			await printt()
		else:
			os.system("clear")
			await printt()
	else:
		logging.basicConfig(
			level = logging.INFO,
			filename = SETTINGS['logs_path'],
			format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
		)
		
	bot = Bot(token = TELEGRAM['token'], parse_mode = ParseMode.HTML, validate_token = True)
	dp = Dispatcher(bot, storage = MemoryStorage())

	db = Database(MYSQL_INFO)
	await db.create_pool()
	await set_default_commands(dp)

	context = {
		"telegram"	: TELEGRAM,
		"settings"	: SETTINGS,
		"broadcast"	: Broadcast()
	}
	dp.middleware.setup(EnvironmentMiddleware(context))
	# dp.middleware.setup(ThrottlingMiddleware())
	dp.middleware.setup(ACLMiddleware(db, dp))
	dp.middleware.setup(UserUpdateMiddleware(db, dp))

	# Регистрируем хендлеры
	register_user(dp)
	register_admin(dp)
	register_errors(dp)
	
	try:
		await dp.skip_updates()
		await dp.start_polling()
	finally:
		await dp.storage.close()
		await dp.storage.wait_closed()
		await bot.session.close()

if __name__ == '__main__':
	try:
		asyncio.run(main())
	except (KeyboardInterrupt, SystemExit):
		pass


# dev t.me/cayse