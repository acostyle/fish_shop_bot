import logging
import redis
from environs import Env
from requests.models import HTTPError

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from validate_email import validate_email

from moltin import (
    create_customer, delete_product_from_cart, get_access_token,
    get_all_products, get_product_by_id, get_product_photo_by_id,
    get_or_create_cart, add_product_to_cart,
    delete_product_from_cart
)
from cart import generate_cart
from keyboard import create_menu_markup


env = Env()
env.read_env()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = env.str('TELEGRAM_BOT_TOKEN')
REDIS_PASSWORD = env.str('REDIS_PASSWORD')
REDIS_HOST = env.str('REDIS_HOST')
REDIS_PORT = env.int('REDIS_PORT')

_database = None


def start(bot, update):
    logger.info('User started bot')
    access_token = get_access_token(_database)
    get_or_create_cart(access_token, update.message.chat_id)
    reply_markup = create_menu_markup(access_token)
    update.message.reply_text(
        reply_markup=reply_markup,
        text='Welcome! Please, choose a fish:',
    )
    return 'HANDLE_MENU'


def handle_menu(bot, update):
    access_token = get_access_token(_database)
    query = update.callback_query

    if query.data == 'cart':
        generate_cart(_database, bot, update)
        return 'HANDLE_CART'
    elif 'page' in query.data:
        page = query.data.split(',')[1]
        reply_markup = create_menu_markup(access_token, int(page))

        bot.edit_message_text(
            text='Welcome! Please, choose a fish:',
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
        )
    
    keyboard = [
        [
            InlineKeyboardButton(
                '1 kg',
                callback_data='1, {0}'.format(query.data),
            ),
            InlineKeyboardButton(
                '5 kg',
                callback_data='5, {0}'.format(query.data),
            ),
            InlineKeyboardButton(
                '10 kg',
                callback_data='10, {0}'.format(query.data),
            ),
        ],
        [InlineKeyboardButton('Menu', callback_data='menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    product = get_product_by_id(access_token, query.data)
    product_photo_id = product['relationships']['main_image']['data']['id']
    product_photo = get_product_photo_by_id(access_token, product_photo_id)
    product_name = product['name']
    product_description = product['description']
    product_price_per_kg = '{0} per kg'.format(
        product['meta']['display_price']['with_tax']['formatted'],
    )
    product_in_stock = product['meta']['stock']['availability']
    if product_in_stock == 'in-stock':
        kg_on_stock = '{0} on stock'.format(
            product['meta']['stock']['level'],
        )
    else:
        kg_on_stock = 'Product is out of stock'

    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=product_photo,
        reply_markup=reply_markup,
        caption='{0}\n{1}\n{2}\n{3}'.format(
            product_name,
            product_price_per_kg,
            kg_on_stock,
            product_description,
        ),
    )

    bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    access_token = get_access_token(_database)
    query = update.callback_query

    if query.data == 'menu':
        reply_markup = create_menu_markup(access_token)
        bot.send_message(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            text='Welcome! Please, choose a fish:',
        )
        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

        return 'HANDLE_MENU'
    elif query.data == 'cart':
        generate_cart(_database, bot, update)

        return 'HANDLE_CART'

    product_quantity, product_id = query.data.split(', ')
    add_product_to_cart(
        access_token,
        query.message.chat_id,
        product_id,
        int(product_quantity),
    )

    return 'HANDLE_MENU'


def handle_cart(bot, update):
    access_token = get_access_token(_database)
    query = update.callback_query

    if query.data == 'menu':
        products = get_all_products(access_token)
        keyboard = [
            [
                InlineKeyboardButton(
                    product['name'],
                    callback_data=product['id'],
                )
                for product in products
            ],
            [InlineKeyboardButton('Cart 🛒', callback_data='cart')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            text='Welcome! Please, choose a fish:',
        )
        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

        return 'HANDLE_MENU'
    elif query.data == 'pay':
        bot.edit_message_text(
            text='Please, send your email',
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

        return 'WAITING_EMAIL'
    
    delete_product_from_cart(
        access_token,
        query.message.chat_id,
        query.data,
    )
    generate_cart(_database, bot, update)

    return 'HANDLE_CART'


def handle_email(bot, update):
    access_token = get_access_token(_database)
    email = update.message.text
    is_valid = validate_email(email)
    if is_valid:
        try:
            create_customer(access_token, str(update.message.chat_id), email)
        except HTTPError:
            update.message.reply_text('Try again!')
            return 'WAITING EMAIL'

        update.message.reply_text(
            text='Manager will text you on this email: {0}'.format(email),
        )
        logger.info('User sent email')
        start(bot, update)

        return 'HANDLE_DESCRIPTION'

    update.message.reply_text('Error! Not valid email')
    logger.info('User sent not valid email')
    return 'WAITING EMAIL'


def handle_users_reply(bot, update):
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
        user_state = _database.get(chat_id)

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        _database.set(chat_id, next_state)
    except Exception as err:
        logger.error(err)


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
    return _database


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    get_database_connection()
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    updater.start_polling()


if __name__ == '__main__':
    main()
