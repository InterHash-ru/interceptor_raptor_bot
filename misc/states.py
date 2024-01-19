from aiogram.dispatcher.filters.state import StatesGroup, State

class StatesActivate(StatesGroup):
	get_token = State()
	get_group = State()
	get_toSend = State()
	get_chatID = State()
	get_keyword = State()
	get_stopWord = State()
	get_crm_link = State()
	get_apiID = State()
	get_api_hash = State()
	# authorized
	get_session = State()
	save_settings = State()
	sign_in = State()

class StatesEditValue(StatesGroup):
	get_trackedGroup = State()
	get_forTransfer = State()
	get_keyWord = State()
	get_keyStopWord = State()

class StatesRun(StatesGroup):
	active = State()

class StatesBroadcast(StatesGroup):
	action = State()
	message = State()
	editor = State()
	keyboard = State()
	timeout = State()
