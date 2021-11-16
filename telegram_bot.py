import redis

from environs import Env

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from moltin import get_auth_token, get_all_products, get_product_by_id, get_product_photo_by_id


env = Env()
env.read_env()

TELEGRAM_TOKEN = env.str('TELEGRAM_BOT_TOKEN')
REDIS_PASSWORD = env.str('REDIS_PASSWORD')
REDIS_HOST = env.str('REDIS_HOST')
REDIS_PORT = env.int('REDIS_PORT')
ACCESS_TOKEN = get_auth_token()

_database = None


def start(bot, update):
    products = get_all_products(ACCESS_TOKEN)
    keyboard = [
        [
            InlineKeyboardButton(product['name'], callback_data=product['id']) 
            for product in products
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Привет!', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query
    product_by_id = get_product_by_id(ACCESS_TOKEN, query.data)
    product_photo_id = product_by_id['relationships']['main_image']['data']['id']
    product_photo = get_product_photo_by_id(ACCESS_TOKEN, product_photo_id)
    product_name = product_by_id['name']
    product_description = product_by_id['description']
    product_price_per_kg = '{0} per kg'.format(
        product_by_id['meta']['display_price']['with_tax']['formatted'],
    )
    product_in_stock = product_by_id['meta']['stock']['availability']
    if product_in_stock == 'in-stock':
        kg_on_stock = '{0} on stock'.format(
            product_by_id['meta']['stock']['level'],
        )
    else:
        kg_on_stock = 'Product is out of stock'

    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=product_photo,
        caption="{0}\n{1}\n{2}\n{3}".format(
            product_name,
            product_price_per_kg,
            kg_on_stock,
            product_description,
        ),
    )

    return "START"


def handle_users_reply(bot, update):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = REDIS_PASSWORD
        database_host = REDIS_HOST
        database_port = REDIS_PORT
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    updater.start_polling()