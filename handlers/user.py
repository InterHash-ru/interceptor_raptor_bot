import os
import io
import re
import ast
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

# FILES <
from misc.help import keyboard_gen, format_number
from misc.filters import IsPrivate, IsAdmin
from misc.states import StatesActivate, StatesRun, StatesEditValue
# FILES >

from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest

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

async def check_key_word(message, bot_conf):
	key_word = ast.literal_eval(bot_conf['key_word'])
	keyStop_word = ast.literal_eval(bot_conf['keyStop_word'])
	message = message.split()
	
	unique_array = set()
	for word in message:
		if word.lower() in key_word and word.lower() not in keyStop_word:
			unique_array.add("#" + word.lower())
	return list(unique_array)


#
# HANDLERS USERS
#

async def command_start(message: types.Message, db, dp, user_info, telegram):
	if user_info['token_id']:
		if user_info['active'] == 0:
			conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
			if conf:

				conf['tracked_groups'] = ast.literal_eval(conf['tracked_groups'])
				conf['chats_for_transfer'] = ast.literal_eval(conf['chats_for_transfer'])
				conf['key_word'] = ast.literal_eval(conf['key_word'])
				conf['keyStop_word'] = ast.literal_eval(conf['keyStop_word'])
				text = '\n'.join([
					hbold("⚙️ Настройки конфигурации перехватчика"),
					"",
					"📤 Откуда будут перехватываться:",
					"\n".join(hcode(str(group)) for group in conf['tracked_groups']),
					"📥 Куда будут приходить:",
					" ".join(hcode(str(chatID)) for chatID in conf['chats_for_transfer']),
					"",
					"🔎 Список ключевых слов - " + hcode("".join(str(len(conf['key_word'])))) + hitalic(' слов'),
					"🛑 Список ключ.стоп-слов - " + hcode("".join(str(len(conf['keyStop_word'])))) + hitalic(' слов'),
					"",
					"🤖 Сессия Клиента Телеграм - " + hcode(str(conf['session_file'])),
					"",
					"🆔 API_ID: " + hcode(str(conf['api_id'])),
					"#️⃣ API_HASH: " + hcode(str(conf['api_hash'])),
						])

				await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['🟢 Запустить перехват'], ['🎛 Настройки']], user_info['is_admin']))
		elif user_info['active'] == 1:
			await show_running(message, db, dp, user_info, telegram)
	else:
		text = "\n".join([
			"👋 Привет, " + hbold(user_info['username']) + "!",
			"",
			"🥷 Этот бот перехватывает сообщения из чатов по нужным параметрам",
			"🔑 Для доступа необходимо активировать токен доступа",
		])
		await message.bot.send_message(user_info['chat_id'], text = text, reply_markup = keyboard_gen([['🔐 Активировать']], user_info['is_admin']), disable_web_page_preview = True)

async def show_running(message: types.Message, db, dp, user_info, telegram):
	conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
	if conf:
		conf['tracked_groups'] = ast.literal_eval(conf['tracked_groups'])
		conf['chats_for_transfer'] = ast.literal_eval(conf['chats_for_transfer'])
		conf['key_word'] = ast.literal_eval(conf['key_word'])
		conf['keyStop_word'] = ast.literal_eval(conf['keyStop_word'])
		text = '\n'.join([
			hbold("🟢 Бот активно работает"),
			"",
			"📤 Какие группы отслеживаются:",
			"\n".join(hcode(str(group)) for group in conf['tracked_groups']),
			"📥 Куда перехвачивает:",
			" ".join(hcode(str(chatID)) for chatID in conf['chats_for_transfer']),
			"",
			"🔎 Список ключевых слов - " + hcode("".join(str(len(conf['key_word'])))) + hitalic(' слов'),
			"🛑 Список ключ.стоп-слов - " + hcode("".join(str(len(conf['keyStop_word'])))) + hitalic(' слов'),
			"",
			"🤖 Сессия Клиента Телеграм - " + hcode(str(conf['session_file'])),
			"",
			"🆔 API_ID: " + hcode(str(conf['api_id'])),
			"#️⃣ API_HASH: " + hcode(str(conf['api_hash'])),
				])
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['⏸ Приостановить работу'],['🎛 Настройки']], user_info['is_admin']))

async def settings_bot(message: types.Message, db, dp, user_info, settings, state: FSMContext):
	conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
	
	conf['tracked_groups'] = ast.literal_eval(conf['tracked_groups'])
	conf['chats_for_transfer'] = ast.literal_eval(conf['chats_for_transfer'])
	conf['key_word'] = ast.literal_eval(conf['key_word'])
	conf['keyStop_word'] = ast.literal_eval(conf['keyStop_word'])
	
	text = '\n'.join([
		hbold("⚙️ Настройки ") + str(conf['session_file']),
		"",
		"📤 Откуда будут перехватываться:",
		"\n".join(hcode(str(group)) for group in conf['tracked_groups']),
		"📥 Куда будут приходить:",
		" ".join(hcode(str(chatID)) for chatID in conf['chats_for_transfer']),
		"",
		"🔎 Список ключевых слов - " + hcode("".join(str(len(conf['key_word'])))) + hitalic(' слов'),
		"🛑 Список ключ.стоп-слов - " + hcode("".join(str(len(conf['keyStop_word'])))) + hitalic(' слов'),
		])

	text_two = '\n'.join([
		hbold("Изменять настройки перехватчика можно в реальном времени, когда бот в процессе работы"),
		"",
		hitalic("❕ Будьте внимательны, проверяйте вводимую информацию, для нормальной работы скрипта"),
		"",
		"▪️ Выберите действие",
		])

	await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
	await message.bot.send_message(chat_id = user_info['chat_id'], text = text_two, reply_markup = keyboard_gen([['▪️ Откуда перехватывать','▪️ Куда будут приходить'],['▪️ Список ключевых слов','▪️ Список ключ-стоп-слов']], user_info['is_admin']))

async def edit_tracked_groups(message: types.Message, db, dp, user_info, settings, state: FSMContext):
	text = '\n'.join([
		"📤 Отправьте одним сообщением " + hitalic("(через пробел)") + " НОВЫЙ список ссылок на телеграм группы " + hitalic("(чаты)") + ", откуда будут перехвачиваться сообщения.",
		"",
		hitalic("▪️ Пример ссылки: ") + hcode("https://t.me/+6WpLeUmqOQA1ZDgy"),
		hitalic("▪️ Клиент уже должен быть участником группы."),
		hitalic("▪️ Поддерживаются ссылки с публичных."),
		])
	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✖️ Отменить']]))
	await StatesEditValue.get_trackedGroup.set()

async def update_tracked_groups(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text == '✖️ Отменить':
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	if await is_valid_url(message.text.split()):
		await db.update_tracked_groups(chat_id = user_info['chat_id'], value = message.text.split())
		text = '\n'.join([
			hbold("✅ Данные успешно обновлены")
			])
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	else:
		await message.reply(text = hbold("💢 Ошибка! Проверьте вводимые данные.\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def edit_forTransfer(message: types.Message, db, dp, user_info, settings, state: FSMContext):
	text = '\n'.join([
		hbold("📥 Пришлите НОВЫЕ CHAT_ID или CHANNEL_ID, куда будут приходить перехваченные сообщения."),
		"Пример ID: " + hcode("-1001616413892"),
		"",
		"❗️ Бот должен быть " + hbold("участником") + " группы или иметь права " + hbold("администратора") + " в канале.",
		"❗️ Это обязательное требование, для работы скрипта.",
		"",
		hitalic("❔ Бот самостоятельно проверяет является ли участником группы или наличие адм.прав"),
		hitalic("❔ Можете добавить сразу несколько в одном сообщении через пробел"),
		hitalic("❔ Необходимы только права публикации сообщений в канале"),
		])

	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✖️ Отменить']]))
	await StatesEditValue.get_forTransfer.set()

async def update_forTransfer(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text == '✖️ Отменить':
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	if await is_valid_ID(message.text.split()):
		await db.update_forTransfer(chat_id = user_info['chat_id'], value = str(message.text.split()))
		text = '\n'.join([
			hbold("✅ Данные успешно обновлены")
			])
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	else:
		await message.reply(text = hbold("💢 Ошибка! Проверьте вводимые данные.\n") + hitalic("(Убедитесь что ID не дублируются. Формат ID: ")+ hcode("'-1234567890000')"))

async def edit_keyWord(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	text = '\n'.join([
		hbold("📝 Отправьте одним сообщением (через пробел) список ключевых слов для поиска"),
		"",
		"📃 Можете отправить файл формата .txt со списком слов",
		])
	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✖️ Отменить']]))
	await StatesEditValue.get_keyWord.set()

async def update_keyWord(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text == '✖️ Отменить':
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	if message.text:
		text = '\n'.join([
			"✅ Ключевые слова добавлены",
			"",
			"В отслеживаемых группах, все новые сообщения будут проверятся на наличие слов:",
			"",
			f"{hcode(message.text)}"
			])
		await db.update_keyWord(chat_id = user_info['chat_id'], value = message.text.split())
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await state.finish()
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
			await db.update_keyWord(chat_id = user_info['chat_id'], value = file_content.split())
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается текст или файл формата .txt\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def edit_key_StopWord(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	text = '\n'.join([
		hbold("📝 Отправьте одним сообщением список ключевых STOP-слов"),
		"",
		"📃 Можете отправить файл формата .txt со списком слов",
		"✉️ Сообщения с наличием таких слов, будут игнорированы",
		])
	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✖️ Отменить']]))
	await StatesEditValue.get_keyStopWord.set()

async def update_key_StopWord(message: types.Message, db, dp, user_info, telegram, state: FSMContext):
	if message.text == '✖️ Отменить':
		await state.finish()
		await show_running(message, db, dp, user_info, telegram)
		return
	if message.text:
		await db.update_keyStopWord(chat_id = user_info['chat_id'], value = message.text.split())
		text = '\n'.join([
			"✅ Список стоп-слов добавлен",
			"",
			"Сообщения с наличием таких слов, будут игнорированы",
			"",
			f"{hcode(message.text)}"
			])
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
		await state.finish()
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
			await db.update_keyStopWord(chat_id = user_info['chat_id'], value = file_content.split())
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text)
			os.remove(file_path_on_server)
			await state.finish()
			await show_running(message, db, dp, user_info, telegram)
#
# RUN INTECEPTOR
#

async def run_intecepter_bot(message: types.Message, db, dp, user_info, settings, state: FSMContext):
	bot_conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
	session_directory = settings['session_path'] + bot_conf['session_file']

	try:
		client = TelegramClient(session_directory, bot_conf['api_id'], bot_conf['api_hash'])
		await client.start()
		dp['data'] = client

		text = '\n'.join([
			hbold("✅ Бот в реальном времени отслеживает чаты"),
			])

		await db.update_running_param(chat_id = user_info['chat_id'], active = 1)
		await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['⏸ Приостановить работу'],['🎛 Настройки']], user_info['is_admin']))
		await register_user_telethon(client, db, message, user_info)  # RUN BOT
	except Exception as error:
		await message.answer(hbold("⚠️ Error: ") + hcode(str(error)))

async def register_user_telethon(client, db, message, user_info):
	bot_conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
	@client.on(events.NewMessage)
	async def my_event_handler(event):
		tracked_groups = ast.literal_eval(bot_conf['tracked_groups'])
		array = []
		for item in tracked_groups:
			try:
				chat_info = await client.get_entity(item.split('https://t.me/')[1])
				chat_info = await client.get_entity(chat_info)
				array.append("-100" + str(chat_info.id))
			except Exception as e:
				print(f"Ошибка: {e}")
		await handle_new_message(client, event, db, array, message, user_info)

async def handle_new_message(client, event, db, tracked_groups, message, user_info):
	bot_conf = await db.get_settings_byUser(chat_id = user_info['chat_id'])
	if str(event.chat_id) in tracked_groups:
		dialogs = await client.get_dialogs()
		for dialog in dialogs:
			channel_id = "-100" + str(event.peer_id.channel_id)
			if str(dialog.id) == str(channel_id):
				consilience = await check_key_word(event.message.message, bot_conf)
				if consilience:
					sender_info = await client.get_entity(event.message.from_id)
					if sender_info.bot == False:

						text_message = event.message.message.split()
						text_message = ' '.join(text_message[:15])
						
						keyboard = types.InlineKeyboardMarkup()
						keyboard.add(types.InlineKeyboardButton("Message in the chat", url = "t.me/" + str(dialog.entity.username) + "/" + str(event.id)))

						text = '\n'.join([
							hbold("💬 Chat Name: ") + str(dialog.name),
							hbold("🆔 Chat ID: ") + hcode(str(dialog.id)),
							"",
							hbold("👤 Sender Name: ") + str(sender_info.first_name),
							hbold("#️⃣ User ID: ") + hcode(str(sender_info.id)),
							hbold("🧑🏻‍💻 Username: ") + "@" + str(sender_info.username),
							hbold("☎️ Phone: ") + hcode(str(sender_info.phone)),
							"",
							hbold("📝 Message: ") + hitalic(text_message + "..."),
							hbold("🔑 Keys: ") + " ".join((item) for item in consilience),
							])

						chats_for_transfer = ast.literal_eval(bot_conf['chats_for_transfer'])
						for chat_id in chats_for_transfer:
							await message.bot.send_message(chat_id = chat_id, text = text, reply_markup = keyboard, disable_web_page_preview = True)

async def stop_intecepter_bot(message: types.Message, db, dp, user_info, settings, telegram):
	if dp['data']:
		client = dp['data']
		await client.disconnect()

	await db.update_running_param(chat_id = user_info['chat_id'], active = 0)
	text = '\n'.join([
		("⏸ Работа перехватчика приостановлена"),
		])

	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['🟢 Запустить перехват'], ['🎛 Настройки']], user_info['is_admin']))
	return

#
# SETTINGS INTECEPTOR
#

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
					hitalic("▪️ Клиент уже должен быть участником группы."),
					hitalic("▪️ Поддерживаются ссылки с публичных."),
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

		if message.text == "https://t.me/username":
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
				"🔎 Список ключевых слов - " + hcode("".join(str(len(array['key_word'])))) + hitalic(' слов'),
				"🛑 Список ключ.стоп-слов - " + hcode("".join(str(len(array['stop_word'])))) + hitalic(' слов'),
				"",
				"🤖 Сессия Клиента Телеграм - " + hcode(str(message.document.file_name)),
				"",
				"🆔 API_ID: " + hcode(str(array['api_id'])),
				"#️⃣  API_HASH: " + hcode(str(array['api_hash'])),
				])
			await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['✅ Завершить настройку']]))
			await StatesActivate.save_settings.set()

	else:
		await message.reply(text = hbold("💢 Неверный формат данных.\n📝 Поддерживается файл формата .session\n") + hitalic("☝️ (Следуйте вышеуказанным инструкциям)"))

async def save_settings(message: types.Message, db, dp, user_info, telegram, settings, state: FSMContext):
	if message.text:
		if message.text == "/start":
			await message.reply(text = hbold("❗️ Вы пытаетесь перезапустить бота"))
			return
		if message.text == "✅ Завершить настройку":
			async with state.proxy() as array:
				try:
					await db.add_new_settings(chat_id = user_info['chat_id'], token = array['token'], tracked_groups = array['groups'], chats_for_transfer = array['chat_id'], key_word = array['key_word'], keyStop_word = array['stop_word'], session_file = array['session_file'], api_id = array['api_id'], api_hash = array['api_hash'])
					tokenID = await db.get_idToken(token = array['token'])
					await db.update_user_tokenID(token_id = tokenID['id'], chat_id = user_info['chat_id'])
				except Exception as error:
					print(error)

				text = '\n'.join([
					"✅ Настройки успешно сохранены в базу данных.",
					"",
					"💡 Токен-доступа Активирован.",
					"⏳ Время жизни токена состовляет 30 дней.",
					])
				await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard_gen([['/start']]))
				await state.finish()
				return
	else:
		await message.reply(text = hitalic("👇 (Используйте кнопки внизу)"))


def register_user(dp: Dispatcher):
	dp.register_message_handler(command_start, CommandStart(), IsPrivate())
	# settings
	dp.register_message_handler(settings_bot, IsPrivate(), state = "*", text = "🎛 Настройки")
	dp.register_message_handler(edit_tracked_groups, IsPrivate(), state = "*", text = "▪️ Откуда перехватывать")
	dp.register_message_handler(update_tracked_groups, IsPrivate(), state = StatesEditValue.get_trackedGroup)
	dp.register_message_handler(edit_forTransfer, IsPrivate(), state = "*", text = "▪️ Куда будут приходить")
	dp.register_message_handler(update_forTransfer, IsPrivate(), state = StatesEditValue.get_forTransfer)
	dp.register_message_handler(edit_keyWord, IsPrivate(), state = "*", text = "▪️ Список ключевых слов")
	dp.register_message_handler(update_keyWord, IsPrivate(), state = StatesEditValue.get_keyWord)
	dp.register_message_handler(edit_key_StopWord, IsPrivate(), state = "*", text = "▪️ Список ключ-стоп-слов")
	dp.register_message_handler(update_key_StopWord, IsPrivate(), state = StatesEditValue.get_keyStopWord)
	# settings
	dp.register_message_handler(run_intecepter_bot, IsPrivate(), text = "🟢 Запустить перехват")
	dp.register_message_handler(stop_intecepter_bot, IsPrivate(), text = "⏸ Приостановить работу")

	# settings inteceptor
	dp.register_message_handler(activate_token, IsPrivate(), text = "🔐 Активировать")
	dp.register_message_handler(check_valide_token, IsPrivate(), state = StatesActivate.get_token, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_group_links, IsPrivate(), state = StatesActivate.get_group, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_chatId_receiver, IsPrivate(), state = StatesActivate.get_chatID, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_key_word, IsPrivate(), state = StatesActivate.get_keyword, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_stop_word, IsPrivate(), state = StatesActivate.get_stopWord, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_apiID, IsPrivate(), state = StatesActivate.get_apiID, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_api_hash, IsPrivate(), state = StatesActivate.get_api_hash, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(get_session, IsPrivate(), state = StatesActivate.get_session, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(save_settings, IsPrivate(), state = StatesActivate.save_settings, content_types = types.ContentTypes.ANY)

	# handlers admin
	dp.register_message_handler(command_start, IsPrivate(), text = "◀️ Главное меню")



	# dev t.me/cayse