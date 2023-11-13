import sys
import os
import asyncio
import pandas as pd

from os import system
from colorama import Fore, Back, Style, init
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import InviteHashExpiredError



class TelegramScrapper():
	def __init__(self, api_id, api_hash):
		self.Client = TelegramClient('test_session/+380732198350.session', api_id, api_hash)
		self.public_chat = 'https://t.me/+UQ9oRTA15ZcyMjQy'
		self.private_chat = 'https://t.me/BinanceUkrainian'
		# self.chat_id = '-1002075626448'

		self.chat_id = ['-1001365086777', '-1001928536131', '-1001216652106', '-1001628671380', '-1001210673317']

	async def printtitle(self):
		system(f"title Soft - Telegram Inteceptor v0.2  \\ Total Track - " + str(len(self.chat_id)) + " chats")
		me = await self.Client.get_me()
		bot_info = '\n'.join([
			f"\nBOT ID: {Style.RESET_ALL + str(me.id) + Fore.GREEN} | PHONE: {Style.RESET_ALL + str(me.phone) + Fore.GREEN} | FIRST NAME: {Style.RESET_ALL + str(me.first_name) + Fore.GREEN}\n"
			])
		print(Fore.GREEN + f"""
███ ████    ███ █  █ ███ ███ ████ ███ ████ ███ ████ ████
 █  █        █  ██ █  █  █   █  █ █   █  █  █  █  █ █  █
 █  █ ██ ██  █  █ ██  █  ███ █    ███ ████  █  █  █ ████
 █  █  █     █  █  █  █  █   █  █ █   █     █  █  █ █ █ 
 █  ████    ███ █  █  █  ███ ████ ███ █     █  ████ █ █ 

{bot_info}

[SELECT ACTION]"""+Style.RESET_ALL+"""
 
  1 - """+Fore.CYAN+"""Get ME"""+Style.RESET_ALL+"""
  2 - """+Fore.CYAN+"""Get Message"""+Style.RESET_ALL+"""
  3 - """+Fore.CYAN+"""Get Participants"""+Style.RESET_ALL+"""
""")



	async def get_me(self):
		me = await self.Client.get_me()
		print("\n\n[ABOUT ME]:\n" + Fore.GREEN, me, Style.RESET_ALL)

	async def get_participants(self):
		try:
			part_item = await self.Client.get_participants(self.private_chat)
		except InviteHashExpiredError:
			print(Fore.RED + "𝐄𝐑𝐑𝐎𝐑!\n" + "Tʜᴇ ᴄʜᴀᴛ ᴛʜᴇ ᴜsᴇʀ ᴛʀɪᴇᴅ ᴛᴏ ᴊᴏɪɴ ʜᴀs ᴇxᴘɪʀᴇᴅ ᴀɴᴅ ɪs ɴᴏᴛ ᴠᴀʟɪᴅ ᴀɴʏᴍᴏʀᴇ (ᴄᴀᴜsᴇᴅ ʙʏ CʜᴇᴄᴋCʜᴀᴛIɴᴠɪᴛᴇRᴇᴏ̨ᴜᴇsᴛ)" + Style.RESET_ALL)
			quit()
		except ValueError:
			await self.Client(ImportChatInviteRequest(hash = self.private_chat.split('+')[1]))
			part_item = await self.Client.get_participants(self.private_chat)

		data_item = []
		for item in part_item:
			data_item.append([item.first_name, "@" + str(item.username), item.id])

		df = pd.DataFrame(data_item, columns = ['first_name', 'username', 'chat_id'])

		print("[PARTICIPANTS]\n" + str(df))
		return

	async def get_old_message(self):
		try:
			part_mes = await self.Client.get_messages(self.private_chat, limit = 50)
		except InviteHashExpiredError:
			print(Fore.RED + "𝐄𝐑𝐑𝐎𝐑!\n" + "Tʜᴇ ᴄʜᴀᴛ ᴛʜᴇ ᴜsᴇʀ ᴛʀɪᴇᴅ ᴛᴏ ᴊᴏɪɴ ʜᴀs ᴇxᴘɪʀᴇᴅ ᴀɴᴅ ɪs ɴᴏᴛ ᴠᴀʟɪᴅ ᴀɴʏᴍᴏʀᴇ (ᴄᴀᴜsᴇᴅ ʙʏ CʜᴇᴄᴋCʜᴀᴛIɴᴠɪᴛᴇRᴇᴏ̨ᴜᴇsᴛ)" + Style.RESET_ALL)
			quit()
		except ValueError:
			await self.Client(ImportChatInviteRequest(hash = self.private_chat.split('+')[1]))
			part_mes = await self.Client.get_messages(self.private_chat, limit = 500)

		data_message = []
		print("\n[OLD MESSAGE IN GROUP (50)]")
		for message in part_mes:
			data_message.append([message.sender_id, message.text])
			print('ID: ' + Fore.RED + str(message.id) + Style.RESET_ALL + " MESSAGE: " + Fore.GREEN + str(message.text) + Style.RESET_ALL)
		# df_message = pd.DataFrame(data_message, columns=['user_id', 'text'])
	

	async def get_about_user(self):
		full = await client(GetFullUserRequest())





	async def run(self):
		await self.Client.start()
		await self.printtitle()
		if not await self.Client.is_user_authorized():
			await self.Client.send_code_request(self.phone)
			await self.Client.sign_in(self.phone, input('Enter the code: '))


		action = input("ENTER ACTION - ")
		if action == '1':
			await self.get_me()
		elif action == '2':
			await self.get_old_message()
		elif action == '3':
			await self.get_participants()

		input("\nPRESS ENTER TO EXIT")
if __name__ == '__main__':
	init()
	os.system("cls")
	Soft = TelegramScrapper(api_id = '23580198', api_hash = 'bdf00d57b3c45da9230e1490c87f51d9')
	asyncio.run(Soft.run())
