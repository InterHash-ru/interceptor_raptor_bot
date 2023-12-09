from datetime import datetime, timedelta
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

class UserUpdateMiddleware(LifetimeControllerMiddleware):
	def __init__(self, db, dp):
		super().__init__()
		self.db = db
		self.dp = dp	

	skip_patterns = ["error", "update"]
	async def post_process(self, obj, data, *args):
		user = data.get('user')
		user_info = data.get('user_info')

		token_list = await self.db.get_all_tokens()
		now = datetime.now()
		if self.db and user and user_info and token_list:
			for token in token_list:
				if now >= token['time_death']:
					await self.db.delete_token(id = token['id'])
					await self.db.delete_settings(token = token['token'])
					token_users = await self.db.get_tokenUsers(id = token['id'])
					for u in token_users:
						await self.db.update_user_tokenID(token_id = 0, chat_id = u['chat_id'])

		if self.db and user and user_info:
			now = datetime.now()
			difference = user_info['date_last_action'] + timedelta(minutes = 30)
			if now > difference:
				await self.db.update_info_user(user.id, user.username, user.full_name, now.strftime('%Y-%m-%d %H:%M:%S'))