from datetime import datetime, timedelta
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

class UserUpdateMiddleware(LifetimeControllerMiddleware):
	skip_patterns = ["error", "update"]

	async def post_process(self, obj, data, *args):
		db = data.get('db')
		user = data.get('user')
		user_info = data.get('user_info')

		token_list = await db.get_all_tokens()
		now = datetime.now()
		if db and user and user_info and token_list:
			for token in token_list:
				if now >= token['time_death']:
					await db.delete_token(id = token['id'])
					token_users = await db.get_tokenUsers(id = token['id'])
					await db.delete_settings(token = token['token'])
					await db.update_user_tokenID(token_id = 0, chat_id = token_users['chat_id'])

		if db and user and user_info:
			now = datetime.now()
			difference = user_info['date_last_action'] + timedelta(minutes = 30)
			if now > difference:
				await db.update_info_user(user.id, user.username, user.full_name, now.strftime('%Y-%m-%d %H:%M:%S'))