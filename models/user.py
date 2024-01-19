import asyncio
import aiomysql

class User:
	# TABLE 'users' INSERT, SELECT
	async def add_new_user(self, chat_id, username, fullname, date_start, from_channel):
		sql = "INSERT INTO users (chat_id, username, fullname, date_start, from_channel) VALUES (%s, %s, %s, %s, %s)"
		return await self.execute(sql, (chat_id, username, fullname, date_start, from_channel), execute = True)

	async def get_info_user(self, **kwargs):
		sql, parameters = self.format_args("SELECT * FROM users WHERE ", kwargs)
		return await self.execute(sql, parameters, fetchone = True)

	async def update_info_user(self, chat_id, username, fullname, date_last_action):
		sql = "UPDATE users SET username = %s, fullname = %s, date_last_action = %s WHERE chat_id = %s"
		return await self.execute(sql, (username, fullname, date_last_action, chat_id), execute = True)

	async def update_kicked_user(self, chat_id, status):
		sql = "UPDATE users SET kicked = %s WHERE chat_id = %s"
		return await self.execute(sql, (status, chat_id), execute = True)

	async def update_running_param(self, chat_id, active):
		sql = "UPDATE users SET active = %s WHERE chat_id = %s"
		return await self.execute(sql, (active, chat_id), execute = True)

	async def update_referrers_user(self, chat_id, count):
		sql = "UPDATE users SET referrers = %s WHERE chat_id = %s"
		return await self.execute(sql, (count, chat_id), execute = True)

	async def update_user_tokenID(self, chat_id, token_id):
		sql = "UPDATE users SET token_id = %s WHERE chat_id = %s"
		return await self.execute(sql, (token_id, chat_id), execute = True)

	async def get_chat_id_users(self, active = False):
		sql = "SELECT chat_id FROM users" + (" WHERE kicked = 0" if active else "")# + " ORDER BY id"
		return await self.execute(sql, fetch = True)

	async def get_is_admin_users(self):
		sql = "SELECT * FROM users WHERE is_admin > 0"
		return await self.execute(sql, fetch = True)

	async def get_black_list_status(self, **kwargs):
		sql, parameters = self.format_args("SELECT * FROM black_list WHERE ", kwargs)
		return await self.execute(sql, parameters, fetchone = True)



	# TABLE 'access' INSERT, SELECT, DELETE
	async def add_new_token(self, token, time_die):
		sql = "INSERT INTO access (token, time_death) VALUES (%s, %s)"
		return await self.execute(sql, (token, time_die), execute = True)

	async def get_all_tokens(self):
		sql = "SELECT * FROM access"
		return await self.execute(sql, fetch = True)

	async def get_tokenInfo(self, id):
		sql = "SELECT * FROM access WHERE id = %s"
		return await self.execute(sql, (id), fetchone = True)
	
	async def update_time_live_token(self, id, datetime):
		sql = "UPDATE access SET time_death = %s WHERE id = %s"
		return await self.execute(sql, (datetime, id), execute = True)

	async def get_idToken(self, token):
		sql = "SELECT * FROM access WHERE token = %s"
		return await self.execute(sql, (token), fetchone = True)

	async def get_tokenUsers(self, id):
		sql = "SELECT * FROM users WHERE token_id = %s"
		return await self.execute(sql, (id), fetch = True)

	async def delete_token(self, id):
		sql = "DELETE FROM access WHERE id = %s"
		return await self.execute(sql, (id), execute = True)

	async def check_token_authenticity(self, token):
		sql = "SELECT * FROM access WHERE token = %s"
		existing = await self.execute(sql, (token), fetchone = True)
		if existing:
			return True
		else:
			return False


	# TABLE 'bot_settings' INSERT, SELECT, DELETE
	async def add_new_settings(self, chat_id, token, tracked_groups, chats_for_transfer, key_word, keyStop_word, crm_url, session_file, api_id, api_hash):
		sql = "INSERT INTO bot_settings (chat_id, token, tracked_groups, chats_for_transfer, key_word, keyStop_word, crm_url, session_file, api_id, api_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		return await self.execute(sql, (chat_id, token, str(tracked_groups), str(chats_for_transfer), str(key_word), str(keyStop_word), str(crm_url), session_file, api_id, api_hash), execute = True)

	async def delete_settings(self, token):
		sql = "DELETE FROM bot_settings WHERE token = %s"
		return await self.execute(sql, (token), execute = True)

	async def get_settings_byUser(self, chat_id):
		sql = "SELECT * FROM bot_settings WHERE chat_id = %s"
		return await self.execute(sql, (chat_id), fetchone = True)

	async def update_tracked_groups(self, chat_id, value):
		sql = "UPDATE bot_settings SET tracked_groups = %s WHERE chat_id = %s"
		return await self.execute(sql, (str(value), chat_id), execute = True)

	async def update_forTransfer(self, chat_id, value):
		sql = "UPDATE bot_settings SET chats_for_transfer = %s WHERE chat_id = %s"
		return await self.execute(sql, (value, chat_id), execute = True)

	async def update_keyWord(self, chat_id, key_word):
		sql = "UPDATE bot_settings SET key_word = %s WHERE chat_id = %s"
		return await self.execute(sql, (str(key_word), chat_id), execute = True)

	async def update_keyStopWord(self, chat_id, keyStop_word):
		sql = "UPDATE bot_settings SET keyStop_word = %s WHERE chat_id = %s"
		return await self.execute(sql, (str(keyStop_word), chat_id), execute = True)

	async def run_time_recording(self, id, time):
		sql = "UPDATE bot_settings SET run_time = %s WHERE id = %s"
		return await self.execute(sql, (time, id), execute = True)


	# TABLE 'unique_users' INSERT, SELECT, DELETE
	async def get_all_unique(self):
		sql = "SELECT * FROM unique_users"
		return await self.execute(sql, fetch = True)

	async def add_new_unique_user(self, chat_id, settings_id, _from, url):
		sql = "INSERT INTO unique_users (chat_id, settings_id, _from, url) VALUES (%s, %s, %s, %s)"
		return await self.execute(sql, (chat_id, settings_id, _from, url), execute = True)


	# ADMIN 'statistics'
	async def get_stats_users(self):
		sql = "SELECT COUNT(*) as all_users, SUM(referrers) as referrers FROM users"
		return await self.execute(sql, fetchrow = True)

	async def get_stats_count(self, table, separator = "=", **kwargs):
		sql = "SELECT COUNT(*) as count FROM {}{}".format(table, (" WHERE " if len(kwargs) else ""))
		sql += " AND ".join([f"{key} {separator} {value}" for key, value in kwargs.items()])
		return await self.execute(sql, fetchrow = True)

# dev t.me/cayse