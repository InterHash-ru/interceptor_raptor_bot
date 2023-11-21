from aiogram.utils.callback_data import CallbackData

pagination_callback = CallbackData("pagination", "action", "page", "all_pages")
show_callback = CallbackData("show", "action")
target_callback = CallbackData("target", "action")
token_callback = CallbackData("token", "action", "id")
period_callback = CallbackData("period", "period", "id")
tokenUsers_callback = CallbackData("tokenUs", "id")
aboutUser_callback = CallbackData("aboutUser", "chatID")
