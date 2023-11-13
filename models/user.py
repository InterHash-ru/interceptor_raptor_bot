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
	async def add_new_token(self, token):
		sql = "INSERT INTO access (token) VALUES (%s)"
		return await self.execute(sql, (token), execute = True)

	async def get_all_tokens(self):
		sql = "SELECT * FROM access"
		return await self.execute(sql, fetch = True)

	async def get_tokenInfo(self, id):
		sql = "SELECT * FROM access WHERE id = %s"
		return await self.execute(sql, (id), fetchone = True)
	
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
	async def add_new_settings(self, chat_id, token, tracked_groups, chats_for_transfer, key_word, keyStop_word, session_file, api_id, api_hash):
		sql = "INSERT INTO bot_settings (self, chat_id, token, tracked_groups, chats_for_transfer, key_word, keyStop_word, session_file, api_id, api_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		return await self.execute(sql, (chat_id, token, str(tracked_groups), str(chats_for_transfer), str(key_word), str(keyStop_word), session_file, api_id, api_hash), execute = True)


	# ADMIN 'statistics'
	async def get_stats_users(self):
		sql = "SELECT COUNT(*) as all_users, SUM(referrers) as referrers FROM users"
		return await self.execute(sql, fetchrow = True)

	async def get_stats_count(self, table, separator = "=", **kwargs):
		sql = "SELECT COUNT(*) as count FROM {}{}".format(table, (" WHERE " if len(kwargs) else ""))
		sql += " AND ".join([f"{key} {separator} {value}" for key, value in kwargs.items()])
		return await self.execute(sql, fetchrow = True)