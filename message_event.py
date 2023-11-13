import os
import pytz
import datetime
from os import system
from telethon.sync import TelegramClient, events
from colorama import Fore, Back, Style, init


api_id = '23580198'
api_hash = 'bdf00d57b3c45da9230e1490c87f51d9'
phone_number = '+380732198350'
chat_id = ['-1001365086777', '-1001928536131', '-1001216652106', '-1001628671380', '-1001210673317']

client = TelegramClient('test_session/+380732198350.session', api_id, api_hash)
client.start()
def printtitle():
	system(f"title Soft - Telegram Inteceptor v0.2  \\ Total Track - " + str(len(chat_id)) + " chats")
	me = client.get_me()
	bot_info = '\n'.join([
		f"		BOT ID: {Style.RESET_ALL + str(me.id) + Fore.GREEN} | PHONE: {Style.RESET_ALL + str(me.phone) + Fore.GREEN} | FIRST NAME: {Style.RESET_ALL + str(me.first_name)}\n"
		])
	print(Fore.GREEN + f"""
		███ ████    ███ █  █ ███ ███ ████ ███ ████ ███ ████ ████
 		 █  █        █  ██ █  █  █   █  █ █   █  █  █  █  █ █  █
 		 █  █ ██ ██  █  █ ██  █  ███ █    ███ ████  █  █  █ ████
 		 █  █  █     █  █  █  █  █   █  █ █   █     █  █  █ █ █ 
 		 █  ████    ███ █  █  █  ███ ████ ███ █     █  ████ █ █ 

{bot_info}


			[Display of Intercepted Messages]
""")


@client.on(events.NewMessage)
async def my_event_handler(event):
	if str(event.chat_id) in chat_id:
		dialogs = await client.get_dialogs()
		for dialog in dialogs:
			channel_id = "-100" + str(event.peer_id.channel_id)
			if str(dialog.id) == str(channel_id):
				print("[NEW MESSAGE]  ID: " + Fore.CYAN + str(event.message.id) + Style.RESET_ALL + " [FROM]: " + Fore.RED + "'" + dialog.name + "'" + Style.RESET_ALL + " [TEXT]: " + Fore.GREEN + event.message.message + Style.RESET_ALL + "  [LINK]: " + Fore.CYAN + "t.me/" + str(dialog.entity.username) + "/" + str(event.id) + Style.RESET_ALL)


init()
os.system("cls")
client.start()
printtitle()
client.run_until_disconnected()

# from telethon.sync import TelegramClient

# api_id = '23580198'
# api_hash = 'bdf00d57b3c45da9230e1490c87f51d9'
# phone_number = '+380732198350'
# chat_id = 'https:://t.me/testpublicgroup12'

# client = TelegramClient('session_name', api_id, api_hash)

# async def get_chat_id():
# 	dialogs = await client.get_dialogs()
# 	for dialog in dialogs:
# 		print(dialog.entity.username)
# 		print()
# 		print()
# 		print()
# 		# print(dialog.name, 'has ID', dialog.id)

# client.start()
# client.loop.run_until_complete(get_chat_id())

