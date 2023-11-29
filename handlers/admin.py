import os
import re
import json
import uuid
import random
import asyncio
import logging
from io import BytesIO
import prettytable as pt
from datetime import datetime, timedelta

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import ctx_data
from aiogram.dispatcher.filters import Command, CommandStart, Text
from aiogram.utils import exceptions
from aiogram.utils.markdown import hbold, hcode, hitalic, hunderline, hstrikethrough, hlink

# FILES <
from misc.filters import IsPrivate, IsAdmin
from misc.help import keyboard_gen, chunks_generators, format_number
from misc.callback_data import show_callback, target_callback, token_callback, pagination_callback, tokenUsers_callback, aboutUser_callback, period_callback
from misc.states import StatesBroadcast
# FILES >

def generate_random_token():
	random_uuid = str(uuid.uuid4())
	random_chars = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(8))
	token = f'{random_chars}-{random_uuid}'
	return token

#
# OTHER
#

async def page_home(message: types.Message, db, dp, user_info, settings):
	if user_info['is_admin'] == 1:
		keyboard = keyboard_gen([['✉️ Рассылка'], ['◀️ Главное меню']])
	else:
		keyboard = keyboard_gen([['🔐 Токены доступа'], ['✉️ Рассылка', '📈 Статистика'], ['📋 Логи ошибок', '🗃 Выгрузить базу'], ['◀️ Главное меню']])
	await message.answer(hbold("💎 " + settings['rights'][user_info['is_admin']] + ", выберите команду для управления."), reply_markup = keyboard)

#
# LOGS
#

async def page_logs(message: types.Message, db, dp, user_info, settings):
	logs_size = os.path.getsize(settings['logs_path'])
	size_kb = round(logs_size / 1024)
	text = "\n".join([
		hbold("📋 Логи ошибок"),
		"",
		hitalic(settings['logs_path']) + " - " + hbold(str(size_kb) + " КБ") ,
	])

	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("📋 Выгрузить лог", callback_data = target_callback.new(action = "logs_download")))
	keyboard.add(types.InlineKeyboardButton("🗑 Очистить лог", callback_data = target_callback.new(action = "logs_clean")))
	await message.answer(text = text, reply_markup = keyboard)

async def callback_logs(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	if callback_data['action'] == "logs_download":
		msg = await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = hbold("⏱ Ожидайте, загружаю информацию"))
		if os.path.getsize(settings['logs_path']):
			file = open(settings['logs_path'], 'rb')
			await call.bot.send_document(chat_id = user_info['chat_id'], document = file, caption = "Дата: " + hbold(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
			await call.bot.delete_message(chat_id = user_info['chat_id'], message_id = msg.message_id)
		else:
			await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = msg.message_id, text = hbold("📋 Логи ошибок пусты!"))
	elif callback_data['action'] == "logs_clean":
		with open(settings['logs_path'], 'w'):
			pass
		await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = hbold("✅ Логи ошибок были очищены!"))

#
# USERS
#

async def page_users(message: types.Message, db, dp, user_info):
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("👥 Всех пользователей", callback_data = target_callback.new(action = "users_download_all")))
	keyboard.add(types.InlineKeyboardButton("👤 Активных пользователей", callback_data = target_callback.new(action = "users_download_active")))
	await message.answer(text = hbold("🗃 Выгрузить базу"), reply_markup = keyboard)

async def callback_users(call: types.CallbackQuery, callback_data: dict, db, dp, user_info):
	msg = await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = hbold("⏱ Ожидайте, загружаю информацию"))
	users = await db.get_chat_id_users(True if callback_data['action'] == "users_download_active" else False)
	count = str(len(users))
	chat_ids = "\n".join([str(user['chat_id']) for user in users])
	file = BytesIO()
	file.write(chat_ids.encode())
	file.seek(0)
	file.name = count + '_users.txt'
	text = "\n".join([
		"Пользователей: " + hbold(count),
		"",
		"Дата: " + hbold(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
	])
	await call.bot.send_document(chat_id = user_info['chat_id'], document = file, caption = text)
	await call.bot.delete_message(chat_id = user_info['chat_id'], message_id = msg.message_id)
	file.close()

#
# STATISTICS
#

async def page_statistics(message: types.Message, db, dp, user_info):
	msg = await message.answer(hbold("⏱ Ожидайте, собираю информацию"))

	stats_users = await db.get_stats_users()
	hour_users = await db.get_stats_count(table = "users", separator = ">=", date_start = "NOW() - INTERVAL 1 HOUR")
	day_users = await db.get_stats_count(table = "users", separator = ">=", date_start = "NOW() - INTERVAL 1 DAY")
	action_day_users = await db.get_stats_count(table = "users", separator = ">=", date_last_action = "NOW() - INTERVAL 1 DAY")
	action = await db.get_stats_count(table = "users", kicked = "0")
	kicked = await db.get_stats_count(table = "users", kicked = "1")
	admins = await db.get_stats_count(table = "users", separator = ">=", is_admin = "1")

	day_users_procent = (day_users['count'] / stats_users['all_users']) * 100
	action_day_users_procent = (action_day_users['count'] / stats_users['all_users']) * 100
	action_procent = (action['count'] / stats_users['all_users']) * 100
	kicked_procent = (kicked['count'] / stats_users['all_users']) * 100

	text = "\n".join([
		hbold("📈 Статистика"),
		"",
		"Общее кол-во пользователей: " + hbold(format_number(stats_users['all_users'])) + hitalic(" чел."),
		"",
		hbold("Кол-во пользователей"),
		hitalic("▪️ новых за последний час: ") + hbold(format_number(hour_users['count'])) + hitalic(" чел."),
		hitalic("▪️ новых за последние 24 часа: ") + hbold(format_number(day_users['count'])) + hitalic(" чел.") + hitalic(" (" + str(round(day_users_procent, 2)) + "%)"),
		hitalic("▪️ пользовались ботом за 24 часа: ") + hbold(format_number(action_day_users['count'])) + hitalic(" чел.") + hitalic(" (" + str(round(action_day_users_procent, 2)) + "%)"),
		hitalic("▪️ которые пользуются ботом: ") + hbold(format_number(action['count'])) + hitalic(" чел.") + hitalic(" (" + str(round(action_procent, 2)) + "%)"),
		hitalic("▪️ которые остановили бота: ") + hbold(format_number(kicked['count'])) + hitalic(" чел.") + hitalic(" (" + str(round(kicked_procent, 2)) + "%)"),
		"",
		hbold("Общее кол-во"),
		hitalic("▫️ администраторов: ") + hbold(format_number(admins['count'])) + hitalic(" чел."),
	])

	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("Администраторы", callback_data = show_callback.new(action = "admins")))
	await message.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = msg.message_id, text = text, reply_markup = keyboard)

async def callback_show_admins(call: types.CallbackQuery, callback_data: dict, db, dp, settings):
	admins = await db.get_is_admin_users()
	text = "📄 Администраторы (" + str(len(admins)) + ")\n\n"
	text += "\n".join([admin['fullname'] + " - " + settings['rights'][admin['is_admin']] for admin in admins])
	await call.bot.answer_callback_query(callback_query_id = call.id, text = text, cache_time = 0, show_alert = True)


#
# ACCESS TOKENS
#

async def page_access_token(message: types.Message, db, dp, user_info, settings):
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("🗂 Посмотреть список", callback_data = token_callback.new(action = "show", id = 'None')))
	keyboard.add(types.InlineKeyboardButton("🔑 Сгенерировать токен", callback_data = token_callback.new(action = "create", id = 'None')))
	
	text = '\n'.join([
		hbold("⚙️ Меню настройки доступа"),
		"",
		"▪️ Выберите действие",
		])
	await message.bot.send_message(chat_id = user_info['chat_id'], text = text, reply_markup = keyboard)

async def create_token_lists(db, user_info, p = 0):
	array = list(chunks_generators(await db.get_all_tokens(), 10))
	pages = len(array)
	pages_count = str(pages - 1)
	keyboard = types.InlineKeyboardMarkup()
	for item in array[p]:
		indicator = " 🟢" if await db.get_tokenUsers(id = item['id']) else " 🔘"
		keyboard.add(
				types.InlineKeyboardButton('🆔: ' + str(item['id']) + "   " + item['token'].split('-')[0] + "...." + item['token'].split('-')[-1][:6] + indicator, callback_data = token_callback.new(action = "about", id = item['id'])))
	keyboard.add(
		types.InlineKeyboardButton("◀️", callback_data = pagination_callback.new(action = 'left', page = p, all_pages = pages_count)),
		types.InlineKeyboardButton(f"{p + 1} / " + str(pages), callback_data = pagination_callback.new(action = 'count', page = 0, all_pages = pages_count)),
		types.InlineKeyboardButton("▶️", callback_data = pagination_callback.new(action = 'right', page = p, all_pages = pages_count))
			)
	return keyboard

async def show_tokens_list(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	tokens = await db.get_all_tokens()
	if tokens:
		try:
			await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = hbold("🗂 Список токенов | Всего ("+ str(len(tokens)) +")"), reply_markup = await create_token_lists(db, user_info))
		except:
			await call.bot.send_message(chat_id = user_info['chat_id'], text = hbold("🗂 Список токенов | Всего ("+ str(len(tokens)) +")"), reply_markup = await create_token_lists(db, user_info))
	else:
		text = '\n'.join([
			"Токенов не найдено 🤷‍♂️",
			"",
			"Создайте новый токен",
			])
		await call.bot.answer_callback_query(callback_query_id = call.id, text = text, cache_time = 0, show_alert = True)

async def about_token(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	if callback_data['action'] == "about":
		token_info = await db.get_tokenInfo(id = callback_data['id'])
		token_users = await db.get_tokenUsers(id = callback_data['id'])
		
		keyboard = types.InlineKeyboardMarkup()
		keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "show", id = 'None')))
		keyboard.add(types.InlineKeyboardButton("⚙️ Продлить время", callback_data = token_callback.new(action = "edit_time", id = callback_data['id'])))
		if token_users:
			keyboard.add(types.InlineKeyboardButton("👨‍💻 Пользователи", callback_data = tokenUsers_callback.new(id = callback_data['id'])))
		keyboard.insert(types.InlineKeyboardButton("🗑 Удалить", callback_data = token_callback.new(action = "attention", id = callback_data['id'])))

		text = '\n'.join([
			hbold("❔ Информация об токене"),
			"",
			"🆔: " + str(token_info['id']),
			"#️⃣  Токен: " + hitalic("(click to copy)\n") + str(hcode(token_info['token'])),
			"📲 Активирован: ДА" if token_users else "📲 Активирован: НЕТ",
			"",
			"📆 Дата создания: " + hitalic(str(token_info['create_time'])),
			"⏳ Активен до: " + str(token_info['time_death'].strftime('%Y-%m-%d')),
			"",
			])
		await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = text, reply_markup = keyboard)

async def edit_time_live_token(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	text = '\n'.join([
		hbold("📆 Выберите период"),
		])
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("7 дней", callback_data = period_callback.new(period = "7", id = callback_data['id'])),
				types.InlineKeyboardButton("10 дней", callback_data = period_callback.new(period = "10", id = callback_data['id'])),
				types.InlineKeyboardButton("20 дней", callback_data = period_callback.new(period = "20", id = callback_data['id'])),
				types.InlineKeyboardButton("30 дней", callback_data = period_callback.new(period = "30", id = callback_data['id'])))
	keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "about", id = callback_data['id'])))
	await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = text, reply_markup = keyboard)

async def update_time_live_token(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	token_info = await db.get_tokenInfo(id = callback_data['id'])
	new_time = token_info['time_death'] + timedelta(days = int(callback_data['period']))
	await db.update_time_live_token(id = callback_data['id'], datetime = new_time)
	await call.bot.answer_callback_query(callback_query_id = call.id, text = "✅ Время жизни токена изменено", cache_time = 0, show_alert = True)
	token_info = await db.get_tokenInfo(id = callback_data['id'])
	token_users = await db.get_tokenUsers(id = callback_data['id'])
	
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "show", id = 'None')))
	keyboard.add(types.InlineKeyboardButton("⚙️ Продлить время", callback_data = token_callback.new(action = "edit_time", id = callback_data['id'])))
	if token_users:
		keyboard.add(types.InlineKeyboardButton("👨‍💻 Пользователи", callback_data = tokenUsers_callback.new(id = callback_data['id'])))
	keyboard.insert(types.InlineKeyboardButton("🗑 Удалить", callback_data = token_callback.new(action = "attention", id = callback_data['id'])))

	text = '\n'.join([
		hbold("❔ Информация об токене"),
		"",
		"🆔: " + str(token_info['id']),
		"#️⃣  Токен: " + hitalic("(click to copy)\n") + str(hcode(token_info['token'])),
		"📲 Активирован: ДА" if token_users else "📲 Активирован: НЕТ",
		"",
		"📆 Дата создания: " + hitalic(str(token_info['create_time'])),
		"⏳ Активен до: " + str(token_info['time_death'].strftime('%Y-%m-%d')),
		"",
		])
	await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = text, reply_markup = keyboard)

async def delete_token(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	if callback_data['action'] == "attention":
		token_info = await db.get_tokenInfo(id = callback_data['id'])
		token_users = await db.get_tokenUsers(id = callback_data['id'])
		
		keyboard = types.InlineKeyboardMarkup()
		keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "show", id = 'None')))
		if token_users:
			keyboard.add(types.InlineKeyboardButton("👨‍💻 Пользователи", callback_data = tokenUsers_callback.new(id = callback_data['id'])))
		keyboard.insert(types.InlineKeyboardButton("🗑 Удалить", callback_data = token_callback.new(action = "delete", id = callback_data['id'])))

		now = datetime.now()
		time_live = now - token_info['create_time'] 

		text = '\n'.join([
			hbold("❔ Информация об токене"),
			"",
			"🆔: " + str(token_info['id']),
			"#️⃣  Токен: " + hitalic("(click to copy)\n") + str(hcode(token_info['token'])),
			"📲 Активирован: ДА" if token_users else "📲 Активирован: НЕТ",
			"",
			"📆 Дата создания: " + hitalic(str(token_info['create_time'])),
			"⏳ Активен до: " + str(token_info['time_death']),
			"",
			])
		await call.bot.answer_callback_query(callback_query_id = call.id, text = "❗️ Будьте внимательны! ❗️\n\nДля удаления нажмите ещё раз", cache_time = 0, show_alert = True)
		await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = text, reply_markup = keyboard)
	elif callback_data['action'] == "delete":
		token_info = await db.get_tokenInfo(id = callback_data['id'])
		token_users = await db.get_tokenUsers(id = callback_data['id'])
		await db.delete_token(id = callback_data['id'])
		try:
			await db.delete_settings(token = token_info['token'])
			await db.update_user_tokenID(token_id = 0, chat_id = token_users['chat_id'])
		except:
			pass
		await call.bot.answer_callback_query(callback_query_id = call.id, text = "♻️ ТОКЕН УДАЛЁН ♻️", cache_time = 0, show_alert = True)
		await call.bot.send_message(chat_id = token_users['chat_id'], text = hbold("❌ Администратор удалил токен доступа"))
		await call.bot.delete_message(chat_id = user_info['chat_id'], message_id = call.message.message_id)
		await show_tokens_list(call, callback_data, db, dp, user_info, settings)
		return

async def tokenUsers_list(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	token_users = await db.get_tokenUsers(id = callback_data['id'])
	keyboard = types.InlineKeyboardMarkup()
	for user in token_users:
		keyboard.add(types.InlineKeyboardButton("👤 " + str(user['username']), callback_data = aboutUser_callback.new(chatID = user['chat_id'])))
	keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "about", id = callback_data['id'])))

	await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = "Кто активировал токен:", reply_markup = keyboard)

async def about_user(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	user = await db.get_info_user(chat_id = callback_data['chatID'])
	keyboard = types.InlineKeyboardMarkup()
	if user['username']:
		keyboard.add(types.InlineKeyboardButton("👤 " + str(user['fullname']), url = "https://t.me/" + user['username']))
	keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data = token_callback.new(action = "about", id = user_info['token_id'])))
	text = '\n'.join([
		"▪️ ID: " + hcode(str(user['chat_id'])),
		"▪️ Fullname: " + hcode(str(user['fullname'])),
		"▪️ Username: @" + str(user['username']),
		"",
		"▪️ Первый запуск бота: " + hcode(str(user['date_start'])),
		"▪️ Последняя активность: " + hcode(str(user['date_last_action'])),
		])

	await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = text, reply_markup = keyboard)

async def create_new_token(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	msg = await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = call.message.message_id, text = "⌨️", reply_markup = None)
	token = generate_random_token()

	time_now = datetime.now()
	time_die_token = time_now + timedelta(days = 30)

	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton("🗂 Посмотреть список", callback_data = token_callback.new(action = "show", id = 'None')))
	text = '\n'.join([
		hbold("✅ Новый токен сгенерирован"),
		"",
		"#️⃣  " + hcode(str(token)),
		hitalic("(click to copy)\n"),
		"",
		"⌚️ Время создания: " + hcode(str(time_now.strftime('%Y-%m-%d %H:%M:%S'))),
		"⌚️ Токен активен до: " + hcode(str(time_die_token.strftime('%Y-%m-%d'))),
		])
	await db.add_new_token(token = token, time_die = time_die_token.strftime('%Y-%m-%d %H:%M:%S'))
	await asyncio.sleep(2)
	await call.bot.edit_message_text(chat_id = user_info['chat_id'], message_id = msg.message_id, text = text, reply_markup = keyboard)

async def callback_pagination(call: types.CallbackQuery, callback_data: dict, db, dp, user_info, settings):
	if callback_data['action'] == "count":
		await call.bot.answer_callback_query(callback_query_id = call.id, text = 'Это просто счетчик страниц 😇', cache_time = 0, show_alert = True)
		return
	if callback_data['action'] == "left":
		if callback_data['page'] == "0":
			await call.bot.delete_message(chat_id = user_info['chat_id'], message_id = call.message.message_id)
			await page_access_token(call, db, dp, user_info, settings)
		markup = await create_token_lists(db, user_info, int(callback_data['page']) - 1)
	elif callback_data['action'] == "right":
		if callback_data['page'] == callback_data['all_pages']:
			await call.bot.answer_callback_query(callback_query_id = call.id, text = 'Больше страниц нету 🙄', cache_time = 0, show_alert = True)
			return
		markup = await create_token_lists(db, user_info, int(callback_data['page']) + 1)

	await call.bot.edit_message_text(
		chat_id			= user_info['chat_id'],
		message_id		= call.message.message_id,
		text			= hbold("Список токенов"),
		reply_markup	= markup
		)

#
# BROADCAST
#

async def page_broadcast(message: types.Message, db, dp, user_info, settings, broadcast):
	if broadcast.status == "available" or broadcast.status == "stopped":
		text = hbold("✉️ Рассылка не запущена")
		keyboard = keyboard_gen([['✉️ Запустить рассылку'], ['◀️ Назад']])
	elif broadcast.status == "launched":
		text = "\n".join([
			hbold("⏳ Сейчас рассылка запущена"),
			"",
			hitalic("🔄 Осталось: ") + hbold(broadcast.stats_left),
			hitalic("✅ Успешно: ") + hbold(broadcast.stats_success),
			hitalic("❌ Неуспешно: ") + hbold(broadcast.stats_fail),
			"",
			hitalic("⏱ Время рассылки: ") + hbold(str(datetime.now() - broadcast.timer['date_start']).split(".")[0]),
			"",
			hbold("Используйте:"),
			hitalic("/edit - чтобы изменить сообщение"),
			hitalic("/stop - чтобы остановить рассылку"),
		])
		keyboard = keyboard_gen([['◀️ Назад']])
	elif broadcast.status == "waiting":
		text = "\n".join([
			hbold("⏱ Рассылка отложенна на: ") + hitalic(broadcast.timer['date']),
			"",
			hbold("Используйте:"),
			hitalic("/cancel - чтобы отменить рассылку"),
		])

		keyboard = keyboard_gen([['◀️ Назад']])
	await message.answer(text = text, reply_markup = keyboard)
	await StatesBroadcast.action.set()

async def page_broadcast_action(message: types.Message, db, dp, user_info, settings, broadcast, state: FSMContext):
	if message.content_type in ["text"]:
		if message.text == "◀️ Назад":
			await state.finish()
			await page_home(message, db, dp, user_info, settings)
			return
		elif message.text == "✉️ Запустить рассылку":
			if broadcast.status == "available":
				await message.answer(text = hbold("✍️ Введите сообщение для рассылки:"), reply_markup = keyboard_gen([['⛔️ Отмена']]))
				await StatesBroadcast.message.set()
			else:
				await state.finish()
				await message.answer(text = hbold("❗️ Запущен другой рекламный пост"), reply_markup = keyboard_gen([['◀️ Назад']]))
		elif message.text == "/edit":
			if broadcast.status == "launched":
				await state.update_data(edit = True)
				await message.answer(text = hbold("✍️ Введите новое сообщение для рассылки:"), reply_markup = keyboard_gen([['⛔️ Отмена']]))
				await StatesBroadcast.message.set()
			else:
				await state.finish()
				await message.answer(text = hbold("❗️ Вы не можете изменить сообщение, рассылка не запущена"), reply_markup = keyboard_gen([['◀️ Назад']]))
		elif message.text == "/stop" or message.text == "/cancel":
			await state.finish()
			broadcast.status = "stopped"
		else:
			await message.answer(text = hbold("❗️ Используйте кнопки ниже"))
	else:
		await message.answer(text = hbold("❗️ Используйте кнопки ниже"))

async def page_broadcast_message(message: types.Message, db, dp, user_info, settings, broadcast, state: FSMContext):
	if message.content_type in ["text"]:
		if message.text == "⛔️ Отмена":
			await state.finish()
			await page_broadcast(message, db, dp, user_info, settings, broadcast)
			return
	
	await state.update_data(message = message, preview = True) if not (await state.get_data()).get("message") else None

	state_data = await state.get_data()
	msgObject = state_data.get("message")
	msgKeyboard = state_data.get("keyboard")
	msgTimer = state_data.get("timer")
	msgEdit = state_data.get("edit")
	msgPreview = state_data.get("preview")
	preview_url = [entities for entities in msgObject.entities if "url" in str(entities)]

	text = "\n".join([
		hbold("⚙️ Настройки рассылки:"),
		"",
		hitalic(" ▫️ Кнопки: ") + hbold("есть" if msgKeyboard else "прикреплены к посту" if msgObject and "reply_markup" in msgObject else "нету"),
		hitalic(" ▫️ Таймер: ") + hbold(msgTimer['date'] if msgTimer else "нету"),
		(hitalic(" ▫️ Предпросмотр ссылок: ") + hbold("выкл" if msgPreview else "вкл") + hitalic(" (/preview - изменить)") + "\n") if len(preview_url) else "",
		hitalic(" ❕ Чтобы сбросить \"Кнопки/Таймер\" нажмите ◀️ Назад"),
		hitalic(" ❕ В пересланном сообщение, кнопками нельзя сбросить") if msgObject and "reply_markup" in msgObject else ""
	])

	if msgEdit:
		keyboard = keyboard_gen([['➕ Добавить кнопки', '👀 Предпросмотр'], ['✉️ Отправить'], ['❌ Отменить']])
	else:
		keyboard = keyboard_gen([['➕ Добавить кнопки', '👀 Предпросмотр'], ['⏱ Таймер', '✉️ Отправить'], ['❌ Отменить']])
	await message.answer(text = text, reply_markup = keyboard)
	await StatesBroadcast.editor.set()

async def page_broadcast_editor(message: types.Message, db, dp, user_info, settings, broadcast, telegram, state: FSMContext):
	if message.content_type in ["text"]:
		state_data = await state.get_data()
		msgObject = state_data.get("message")
		msgKeyboard = state_data.get("keyboard")
		msgEdit = state_data.get("edit")
		msgPreview = state_data.get("preview")

		if message.text in "➕ Добавить кнопки":
			text = "\n".join([
				hbold("➕ Добавить кнопки"),
				"",
				hitalic("❕ Формат: ") + hbold("Текст - ссылка | Текст - ссылка"),
			])
			await message.answer(text = text, reply_markup = keyboard_gen([['◀️ Назад']]))
			await StatesBroadcast.keyboard.set()
		elif message.text in "⏱ Таймер" and not msgEdit:
			text = "\n".join([
				hbold("⏱ Таймер"),
				"",
				hitalic("❕ Формат: ") + hbold("2025-12-01 10:00"),
			])
			await message.answer(text = text, reply_markup = keyboard_gen([['◀️ Назад']]))
			await StatesBroadcast.timeout.set()
		elif message.text in "👀 Предпросмотр":
			try:
				await msgObject.send_copy(chat_id = user_info['chat_id'], reply_markup = msgKeyboard, disable_web_page_preview = msgPreview)
			except:
				await message.answer(text = hbold("❗️ В кнопках указаны некорректные ссылки"))
		elif message.text in "✉️ Отправить":
			if msgEdit:
				await state.finish()
				broadcast.message = msgObject
				broadcast.keyboard = msgKeyboard
				await message.answer(text = hbold("✅ Сообщение успешно изменено!"), reply_markup = keyboard_gen([['◀️ Назад']]))
			else:
				await broadcast_run(message, db, dp, user_info, settings, broadcast, telegram, state)
		elif message.text in "/preview":
			if msgPreview:
				await state.update_data(preview = False)
			else:
				await state.update_data(preview = True)
			await page_broadcast_message(message, db, dp, user_info, settings, broadcast,  state)
		elif message.text in "❌ Отменить":
			await state.finish()
			await page_broadcast(message, db, dp, user_info, settings, broadcast)
			return
		else:
			await message.answer(text = hbold("❗️ Используйте кнопки ниже"))
	else:
		await message.answer(text = hbold("❗️ Используйте кнопки ниже"))

async def page_broadcast_keyboard(message: types.Message, db, dp, user_info, settings, broadcast, state: FSMContext):
	if message.content_type in ["text"]:
		if message.text == "◀️ Назад":
			await state.update_data(keyboard = None) if (await state.get_data()).get("keyboard") else None
			await page_broadcast_message(message, db, dp, user_info, settings, broadcast,  state)
			return
	try:
		keyboard = types.InlineKeyboardMarkup()
		text_buttons = list(filter(None, message.text.split("\n")))
		for text_button in text_buttons:
			more = []
			buttons = text_button.split("|")
			for button in buttons:
				params = button.strip().split("-")
				more.append(types.InlineKeyboardButton(params[0].strip(), url = params[1].strip()))
			keyboard.add(*more)
		await state.update_data(keyboard = keyboard)
		await page_broadcast_message(message, db, dp, user_info, settings, broadcast,  state)
	except Exception as e:
		await message.answer(text = hbold("❗️ Вы отправляете кнопки в неправильном формате"))

async def page_broadcast_timeout(message: types.Message, db, dp, user_info, settings, broadcast, telegram, state: FSMContext):
	if message.content_type in ["text"]:
		if message.text == "◀️ Назад":
			await state.update_data(timer = None) if (await state.get_data()).get("timer") else None
			await page_broadcast_message(message, db, dp, user_info, settings, broadcast,  state)
			return
	try:
		date = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
		seconds_left = int(date.timestamp()) - int(datetime.now().timestamp())
		if seconds_left <= 0:
			await message.answer(text = hbold("❗️ Вы указали некорректную дату."))
			return
		await state.update_data(timer = {"date": date, "seconds_left": seconds_left})
		await page_broadcast_message(message, db, dp, user_info, settings, broadcast,  state)
	except Exception as e:
		await message.answer(text = hbold("❗️ Вы указали некорректную дату."))

async def broadcast_notify(message, action):
	try:
		data = ctx_data.get()
		user_info = data.get('user_info')
		settings = data.get('settings')
		broadcast = data.get('broadcast')
		telegram = data.get('telegram')

		if action == "channel_message":
			broadcast.channel_message = await broadcast.message.send_copy(chat_id = settings['broadcast_channel'], reply_markup = broadcast.keyboard, disable_web_page_preview = broadcast.preview)
			return
		elif action == "launched":
			text = hbold("✅ Рассылка запущена!")
		elif action == "waiting":
			text = hbold("⏱ Рассылка отложенна на: ") + hitalic(broadcast.timer['date'])
		elif action == "waiting_stop":
			text = hbold("⛔️ Отложенная рассылка отменена!")
		elif action == "stopped":
			text = "\n".join([
				hbold("⛔️ Рассылка остановлена!"),
				"",
				hitalic("🔄 Осталось: ") + hbold(broadcast.stats_left),
				hitalic("✅ Успешно: ") + hbold(broadcast.stats_success),
				hitalic("❌ Неуспешно: ") + hbold(broadcast.stats_fail),
			])
		elif action == "finish":
			text = "\n".join([
				hbold("✉️ Рассылка выполнена!"),
				"",
				hitalic("✅ Успешно: ") + hbold(broadcast.stats_success),
				hitalic("❌ Неуспешно: ") + hbold(broadcast.stats_fail),
				"",
				hitalic("⏱ Время рассылки заняло: ") + hbold(str(datetime.now() - broadcast.timer['date_start']).split(".")[0]),
			])

		await message.answer(text, reply_markup = (keyboard_gen([['◀️ Назад']]) if action != "finish" else None))

		text += hitalic("\n\n🤖 Бот: @" + telegram['username'])
		text += hitalic("\n👤 Запустил: ") + hbold(user_info['fullname'])
		await message.bot.send_message(chat_id = settings['broadcast_channel'], reply_to_message_id = broadcast.channel_message.message_id, text = text)
	except Exception as e:
		pass

async def broadcast_sm(chat_id, broadcast):
	try:
		await broadcast.message.send_copy(chat_id = chat_id, reply_markup = broadcast.keyboard, disable_web_page_preview = broadcast.preview)
	except exceptions.RetryAfter as e:
		await asyncio.sleep(e.timeout)
		logging.exception(f'"| Broadcast RetryAfter | - (chat_id: {str(chat_id)}, ERROR: {str(e)}, Broadcast: {str(broadcast.__dict__)})\n\n')
		return await broadcast_sm(chat_id, broadcast)
	except Exception as e:
		broadcast.stats_fail += 1
	else:
		broadcast.stats_success += 1
	broadcast.stats_left -= 1

async def broadcast_run(message: types.Message, db, dp, user_info, settings, broadcast, telegram, state: FSMContext):
	if broadcast.status == "available":
		state_data = await state.get_data()
		if state_data.get("timer"):
			if int(state_data.get("timer")['date'].timestamp()) - int(datetime.now().timestamp()) <= 0:
				await message.answer(text = hbold("❗️ Вы указали некорректную дату."))
				return
		await state.finish()

		broadcast.message = state_data.get("message")
		broadcast.keyboard = state_data.get("keyboard")
		broadcast.timer = state_data.get("timer")
		broadcast.preview = state_data.get("preview")

		await broadcast_notify(message, action = "channel_message")

		if broadcast.timer and broadcast.timer['seconds_left']:
			await broadcast_notify(message, action = "waiting")
			broadcast.status = "waiting"
			for i in range(broadcast.timer['seconds_left']):
				if broadcast.status == "stopped":
					await broadcast_notify(message, action = "waiting_stop")
					broadcast.declare_variables()
					return
				await asyncio.sleep(1)
		
		users = await db.get_chat_id_users(True)
		broadcast.stats_left = len(users)
		if broadcast.timer:
			broadcast.timer.update({"date_start": datetime.now()})
		else:
			broadcast.timer = {"date_start": datetime.now()}

		await broadcast_notify(message, action = "launched")
		broadcast.status = "launched"

		packs = list(chunks_generators(users, settings['broadcast_threads']))

		for users in packs:
			tasks = []
			if broadcast.status == "stopped":
				await broadcast_notify(message, action = "stopped")
				broadcast.declare_variables()
				return
			for user in users:
				tasks.append(asyncio.create_task(broadcast_sm(user['chat_id'], broadcast)))
			await asyncio.gather(*tasks)
			await asyncio.sleep(settings['broadcast_timeout'])

		await broadcast_notify(message, action = "finish")
		broadcast.declare_variables()
	else:
		await state.finish()
		await message.answer(text = hbold("❗️ Запущен другой рекламный пост"), reply_markup = keyboard_gen([['◀️ Назад']]))

def register_admin(dp: Dispatcher):
	# OTHER
	dp.register_message_handler(page_home, IsPrivate(), IsAdmin(1), Text(equals = ["⚙️ Управление", "◀️ Назад"], ignore_case = True))

	# LOGS
	dp.register_message_handler(page_logs, IsPrivate(), IsAdmin(), text = "📋 Логи ошибок")
	dp.register_callback_query_handler(callback_logs, target_callback.filter(action = ["logs_download", "logs_clean"]))

	# USERS
	dp.register_message_handler(page_users, IsPrivate(), IsAdmin(), text = "🗃 Выгрузить базу")
	dp.register_callback_query_handler(callback_users, target_callback.filter(action = ["users_download_all", "users_download_active"]))

	# STATISTICS
	dp.register_message_handler(page_statistics, IsPrivate(), IsAdmin(), text = "📈 Статистика")
	dp.register_callback_query_handler(callback_show_admins, show_callback.filter(action = "admins"))

	# ACCESS TOKEN
	dp.register_message_handler(page_access_token, IsPrivate(), IsAdmin(), text = "🔐 Токены доступа")
	dp.register_callback_query_handler(show_tokens_list, token_callback.filter(action = "show"))
	dp.register_callback_query_handler(about_token, token_callback.filter(action = "about"))
	dp.register_callback_query_handler(edit_time_live_token, token_callback.filter(action = "edit_time"))
	dp.register_callback_query_handler(update_time_live_token, period_callback.filter())
	dp.register_callback_query_handler(delete_token, token_callback.filter(action = ["attention", "delete"]))
	dp.register_callback_query_handler(tokenUsers_list, tokenUsers_callback.filter())
	dp.register_callback_query_handler(about_user, aboutUser_callback.filter())
	dp.register_callback_query_handler(create_new_token, token_callback.filter(action = "create"))
	dp.register_callback_query_handler(callback_pagination, pagination_callback.filter())


	# BROADCAST
	dp.register_message_handler(page_broadcast, IsPrivate(), IsAdmin(1), text = "✉️ Рассылка")
	dp.register_message_handler(page_broadcast_action, IsPrivate(), IsAdmin(1), state = StatesBroadcast.action, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(page_broadcast_message, IsPrivate(), IsAdmin(1), state = StatesBroadcast.message, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(page_broadcast_editor, IsPrivate(), IsAdmin(1), state = StatesBroadcast.editor, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(page_broadcast_keyboard, IsPrivate(), IsAdmin(1), state = StatesBroadcast.keyboard, content_types = types.ContentTypes.ANY)
	dp.register_message_handler(page_broadcast_timeout, IsPrivate(), IsAdmin(1), state = StatesBroadcast.timeout, content_types = types.ContentTypes.ANY)
	
# dev t.me/cayse