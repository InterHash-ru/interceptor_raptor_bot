import os
import io
import re
import json
import asyncio
from datetime import datetime, timedelta

from aiogram import types
from aiogram import Dispatcher
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, CommandStart, Text
from aiogram.utils.markdown import hbold, hcode, hitalic, hunderline, hstrikethrough, hlink
from aiogram.utils.deep_linking import get_start_link

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import InviteHashExpiredError

# FILES <
from misc.help import keyboard_gen, format_number
from misc.filters import IsPrivate, IsAdmin
from misc.states import StatesActivate
# FILES >




#
# HELP FUNC
#

async def is_valid_token(token):
	pattern = r'^[a-z0-9]{8}-[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$'
	return bool(re.match(pattern, token))

async def is_valid_url(message):
	if all('https://t.me/' in url for url in message) and len(message) <= 5:
		return True
	else:
		return False

async def is_valid_ID(message):
	pattern = r'^-\d{13}$'
	seen_ids = set()
	for item in message:
		if re.match(pattern, item):
			if item in seen_ids:
				return False
			seen_ids.add(item)
		else:
			return False
	return True

async def check_rights_bot(list_id, message):
	active_chats = []
	for chat_id in list_id:
		try:
			chat = await message.bot.get_chat(chat_id)
			active_chats.append(chat)
		except Exception:
			continue
	if active_chats:
		return active_chats
	else:
		return False

#
# HANDLERS USERS
#

async def command_start(message: types.Message, db, dp, user_info, telegram):

	# await StatesActivate.get_apiID.set()


	if user_info['token_id']:
		print('avtivated')
	else:
		text = "\n".join([
			"👋 Привет, " + hbold(user_info['username']) + "!",
			"",
			"🥷 Этот бот перехватывает сообщения из чатов по нужным параметрам",
			"🔑 Для доступа необходимо активировать токен доступа",
		])
		await message.bot.send_message(user_info['chat_id'], text = text, reply_markup = keyboard_gen([['🔐 Активировать']], user_info['is_admin']), disable_web_page_preview = True)

async def activate_token(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	text = '\n'.join([
		hbold("🔒 Для получения доступа, необходимо активировать токен"),
		"",
		hitalic("Формат: ") + hcode("XXXXXXXX-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"),
		])

	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['Завершить']])) 
	await StatesActivate.get_token.set()

async def check_valide_token(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text:
		if message.text == "Завершить":
			await state.finish()
			await command_start(message, db, dp, user_info, telegram)
			return

		if message.text == "/start":
			await message.reply(text = hbold("❗️ Вы пытаетесь перезапустить бота"))
			return

		if await is_valid_token(message.text):
			if await db.check_token_authenticity(message.text):
				msg = await message.bot.send_message(chat_id = user_info['chat_id'], text = "🔐", reply_markup = types.ReplyKeyboardRemove())
				await asyncio.sleep(1.8)
				text = '\n'.join([
					hbold("🔓 Токен идентифицирован"),
					"",
					"📤 Отправьте одним сообщением " + hitalic("(через пробел)") + " список ссылок на телеграм группы " + hitalic("(чаты)") + ", откуда будут перехвачиваться сообщения.",
					"",
					hitalic("▪️ Пример ссылки: ") + hcode("https://t.me/+6WpLeUmqOQA1ZDgy"),
					hitalic("▪️ Клиент самостоятельно добавиться во все группы."),
					hitalic("▪️ Макс. кол-во отслеживаемых групп, не более 5️⃣"),
					hitalic("▪️ Поддерживаются ссылки с публичных и приватных групп."),
					])
				await message.bot.delete_message(chat_id = user_info['chat_id'], message_id = msg.message_id)
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text, disable_web_page_preview = True)
				async with state.proxy() as array:
					array['token'] = message.text
				await StatesActivate.get_group.set()
			else:
				await message.reply(text = hbold("🚫 Указанный вами токен доступа не обнаружен в нашей базе данных."))
				await state.finish()
				await command_start(message, db, dp, user_info, telegram)
				return
		else:
			await message.reply(text = hbold("💢 Ошибка формата токена.\nУбедитесь в правильности вводных данных."))
	else:
		await message.reply(text = hbold("💢 Неверный формат.\nTOKEN - это строка, может содержать буквы, цифры и специальные символы"))

async def get_group_links(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text:
		if message.text == "/start":
			await message.reply(text = hbold("❗️ Вы пытаетесь перезапустить бота"))
			return

		if message.text == "https://t.me/+6WpLeUmqOQA1ZDgy":
			await message.reply(text = hbold("❗️ Это ссылка служит примером.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))
			return

		if await is_valid_url(message.text.split()):
			url_list = ""
			for url in message.text.split():
				url_list += "📎 " + hcode("t.me/") + url.split('t.me/')[1] + "\n"
			
			text = '\n'.join([
				hbold("✅ Ссылки успешно добавлены | Всего: " + str(len(message.text.split()))),
				"",
				f"{url_list}",
				])

			msg = await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
			
			text = '\n'.join([
				hbold("📥 Пришлите CHAT_ID или CHANNEL_ID, куда будут приходить перехваченные сообщения."),
				"Пример ID: " + hcode("-1001616413892"),
				"",
				"❗️ Бот должен быть " + hbold("участником") + " группы или иметь права " + hbold("администратора") + " в канале.",
				"❗️ Это обязательное требование, для работы скрипта.",
				"",
				hitalic("❔ Бот самостоятельно проверяет является ли участником группы или наличие адм.прав"),
				hitalic("❔ Можете добавить сразу несколько в одном сообщении через пробел"),
				hitalic("❔ Необходимы только права публикации сообщений в канале"),
				])
			await asyncio.sleep(2)
			msg = await message.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = msg.message_id, text = "📤")
			await asyncio.sleep(2.2)
			await message.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = msg.message_id, text = text)

			async with state.proxy() as array:
				array['groups'] = message.text.split()
			await StatesActivate.get_chatID.set()
		else:
			await message.reply(text = hbold("💢 Ошибка! Проверьте вводимые данные.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def get_chatId_receiver(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text:
		if message.text == "/start":
			await message.reply(text = hbold("❗️ Вы пытаетесь перезапустить бота"))
			return

		if message.text == "-1001616413892":
			await message.reply(text = hbold("❗️ Этот CHAT_ID служит примером.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))
			return
		if await is_valid_ID(message.text.split()):
			active_chats = await check_rights_bot(message.text.split(), message)
			if active_chats:
				chats = ""
				for item in active_chats:
					emoji = "💬 " if item['type'] == "supergroup" else "📮 "
					chats += emoji + "'" + hbold(item['title']) + "'" + " " + hitalic("(" + item['type'] + ")\n")
				text = '\n'.join([
					hbold("✅ Чаты успешно добавлены"),
					"",
					"Перехваченные сообщения будут приходить в:",
					"",
					f"{chats}",
					])
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
				async with state.proxy() as array:
					array['chat_id'] = message.text.split()
					array['chat_id_obj'] = "".join((item['title']) for item in active_chats)
				text = '\n'.join([
					hbold("📝 Отправьте одним сообщением (через пробел) список ключевых слов для поиска"),
					"",
					"📃 Можете отправить файл формата .txt со списком слов",
					])
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
				await StatesActivate.get_keyword.set()
			else:
				await message.reply(text = hbold("⛔️ У бота нет прав доступа к ресурсам!\n")) + hitalic("☝️ (Следуйте вышеуказанным инструкциям)")
		else:
			await message.reply(text = hbold("💢 Ошибка! Проверьте вводимые данные.\n") + hitalic("(Убедитесь что ID не дублируются. Формат ID: ")+ hcode("'-1234567890000')"))

	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def get_key_word(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		text = '\n'.join([
			"✅ Ключевые слова добавлены",
			"",
			"В отслеживаемых группах, все новые сообщения будут проверятся на наличие слов:",
			"",
			f"{hcode(message.text)}"
			])
		async with state.proxy() as array:
			array['key_word'] = message.text.split()
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)

		text = '\n'.join([
			hbold("📝 Отправьте одним сообщением список ключевых STOP-слов"),
			"",
			"📃 Можете отправить файл формата .txt со списком слов",
			"✉️ Сообщения с наличием таких слов, будут игнорированы",
			])
		await asyncio.sleep(1)
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await StatesActivate.get_stopWord.set()

	elif message.document.mime_type == 'text/plain':
		file_id = message.document.file_id
		file_info = await message.bot.get_file(file_id)
		file_path = file_info.file_path
		current_directory = os.getcwd()
		file_path_on_server = os.path.join(current_directory, str(user_info['chat_id']) + '.txt')
		downloaded_file = await message.bot.download_file(file_path)

		with open(file_path_on_server, 'wb') as file:
			file.write(downloaded_file.read())

		with open(file_path_on_server, 'r', encoding = "utf-8") as file:
			file_content = file.read()
			text = '\n'.join([
				"✅ Ключевые слова добавлены",
				"",
				"В отслеживаемых группах, все новые сообщения будут проверятся на наличие слов:",
				"",
				f"{hcode(file_content)}"
				])
		async with state.proxy() as array:
			array['key_word'] = file_content.split()
		try:
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		except:
			pass
		os.remove(file_path_on_server)
		text = '\n'.join([
			hbold("📝 Отправьте одним сообщением список ключевых STOP-слов"),
			"",
			"📃 Можете отправить файл формата .txt со списком слов",
			"✉️ Сообщения с наличием таких слов, будут игнорированы",
			])
		
		await asyncio.sleep(1)
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await StatesActivate.get_stopWord.set()
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст или файл формата .txt\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def get_stop_word(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		text = '\n'.join([
			"✅ Список стоп-слов добавлен",
			"",
			"Сообщения с наличием таких слов, будут игнорированы",
			"",
			f"{hcode(message.text)}"
			])
		async with state.proxy() as array:
			array['stop_word'] = message.text.split()
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)

		text = '\n'.join([
			hbold("🆔 Отправьте API_ID клиента телеграм")
			])
		await asyncio.sleep(1)
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await StatesActivate.get_apiID.set()
	elif message.document.mime_type == 'text/plain':
		file_id = message.document.file_id
		file_info = await message.bot.get_file(file_id)
		file_path = file_info.file_path
		current_directory = os.getcwd()
		file_path_on_server = os.path.join(current_directory, str(user_info['chat_id']) + '.txt')
		downloaded_file = await message.bot.download_file(file_path)

		with open(file_path_on_server, 'wb') as file:
			file.write(downloaded_file.read())

		with open(file_path_on_server, 'r', encoding = "utf-8") as file:
			file_content = file.read()
			text = '\n'.join([
				"✅ Список стоп-слов добавлен",
				"",
				"Сообщения с наличием таких слов, будут игнорированы",
				"",
				f"{hcode(file_content)}"
				])
		async with state.proxy() as array:
			array['stop_word'] = file_content.split()
		try:
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		except:
			pass
		os.remove(file_path_on_server)
		text = '\n'.join([
			hbold("🆔 Отправьте API_ID клиента телеграм")
			])
		await asyncio.sleep(1)
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await StatesActivate.get_apiID.set()
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст или файл формата .txt\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

#
# Authorized
#

async def get_apiID(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		if message.text.isdecimal():
			async with state.proxy() as array:
				array['api_id'] = message.text
				text = '\n'.join([
					hbold("#️⃣  Отправьте API_HASH клиента телеграм"),
					])
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
				await StatesActivate.get_api_hash.set()
		else:
			await message.reply(text = hbold("💢 Неверный формат данных. API ID не может содержать буквы и символы"))
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def get_api_hash(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		async with state.proxy() as array:
			array['api_hash'] = message.text
			text = '\n'.join([
				hbold("🎛 Настройка завершена!"),
				"",
				"👤 Теперь необходимо авторизировать ваш Клиент Телеграм",
				"",
				"📄 Отправьте " + hbold(".session") + " файл сессии аккаунта",
				])
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
			await StatesActivate.get_session.set()
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))


async def get_session(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.document.mime_type == 'application/vnd.sqlite3':
		file_id = message.document.file_id
		file_info = await message.bot.get_file(file_id)
		file_path = file_info.file_path
		current_directory = os.getcwd()
		file_path_on_server = os.path.join(settings['session_path'], message.document.file_name)
		downloaded_file = await message.bot.download_file(file_path)
		with open(file_path_on_server, 'wb') as file:
			file.write(downloaded_file.read())
			file.close()

		async with state.proxy() as array:
			array['session_file'] = message.document.file_name
			text = '\n'.join([
				hbold("⚙️ Настройки конфигурации бота"),
				"",
				"📤 Откуда будут перехватываться:",
				"\n".join(hcode(str(group)) for group in array['groups']),
				"📥 Куда будут приходить:",
				" ".join(hcode(str(chatID)) for chatID in array['chat_id']),
				" ".join(hitalic(str(item)) for item in array['chat_id_obj']),
				"",
				"🔎 Список ключевых слов - " + hcode(str(len("".join(array['key_word'])))) + hitalic(' слов'),
				"🛑 Список ключ.стоп-слов - " + hcode(str(len("".join(array['stop_word'])))) + hitalic(' слов'),
				"",
				"🤖 Сессия Клиента Телеграм - " + hcode(str(message.document.file_name)),
				"",
				"🆔 API_ID: " + hcode(str(array['api_id'])),
				"#️⃣  API_HASH: " + hcode(str(array['api_hash'])),
				])
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✅ Запустить']]))
			await StatesActivate.login.set()

	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается файл формата .session\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))


async def save_settings(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		if message.text == "/start":
			await message.reply(text = hbold("❗️ Вы пытаетесь перезапустить бота"))
			return
		if message.text == "✅ Запустить":
			async with state.proxy() as array:
				await db.add_new_settings(chat_id = user_info['chat_id'], token = array['token'], tracked_groups = array['groups'], chats_for_transfer = array['chat_id'], key_word = array['key_word'], keyStop_word = array['stop_word'], session_file = array['session_file'], api_id = array['api_id'], api_hash = array['api_hash'])
				tokenID = await db.get_idToken(token = array['token'])
				await db.update_user_tokenID(chat_id = user_info['chat_id'], token_id = tokenID)

				text = '\n'.join([
					"✅ Настройки успешно сохранены в базу данных",
					])
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
	else:
		await message.reply(text = hitalic("👇 (Используйте кнопки внизу)"))


def register_user(dp: Dispatcher):
	dp.register_message_handler(command_start, CommandStart(), IsPrivate())

	dp.register_message_handler(activate_token, IsPrivate(), text = "🔐 Активировать")
	dp.register_message_handler(check_valide_token, IsPrivate(), state = StatesActivate.get_token, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_group_links, IsPrivate(), state = StatesActivate.get_group, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_chatId_receiver, IsPrivate(), state = StatesActivate.get_chatID, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_key_word, IsPrivate(), state = StatesActivate.get_keyword, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_stop_word, IsPrivate(), state = StatesActivate.get_stopWord, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_apiID, IsPrivate(), state = StatesActivate.get_apiID, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_api_hash, IsPrivate(), state = StatesActivate.get_api_hash, content_types = types.ContentTypes.ANY)
	# authorizate
	dp.register_message_handler(get_session, IsPrivate(), state = StatesActivate.get_session, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(save_settings, IsPrivate(), state = StatesActivate.login, content_types = types.ContentTypes.ANY)

	# handlers admin
	dp.register_message_handler(command_start, IsPrivate(), text = "◀️ Главное меню")