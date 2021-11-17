import logging
import redis
from environs import Env
from requests.models import HTTPError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from validate_email import validate_email

from moltin import (
    create_customer, delete_product_from_cart, get_auth_token,
    get_all_products, get_product_by_id, get_product_photo_by_id,
    get_or_create_cart, add_product_to_cart, get_cart_items,
    delete_product_from_cart
)


env = Env()
env.read_env()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = env.str('TELEGRAM_BOT_TOKEN')
REDIS_PASSWORD = env.str('REDIS_PASSWORD')
REDIS_HOST = env.str('REDIS_HOST')
REDIS_PORT = env.int('REDIS_PORT')
ACCESS_TOKEN = get_auth_token()

_database = None


def start(bot, update):
    logger.info('User started bot')
    get_or_create_cart(ACCESS_TOKEN, update.message.chat_id)
    products = get_all_products(ACCESS_TOKEN)
    keyboard = [
        [
            InlineKeyboardButton(
                product['name'],
                callback_data=product['id'],
            )
            for product in products
        ],
        [InlineKeyboardButton('Cart', callback_data='cart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        reply_markup=reply_markup,
        text='Welcome! Please, choose a fish:',
    )
    return 'HANDLE_MENU'


def handle_menu(bot, update):
    query = update.callback_query

    if query.data == 'cart':
        generate_cart(bot, update)
        return 'HANDLE_CART'
    
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

    product = get_product_by_id(ACCESS_TOKEN, query.data)
    product_photo_id = product['relationships']['main_image']['data']['id']
    product_photo = get_product_photo_by_id(ACCESS_TOKEN, product_photo_id)
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

    bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )
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

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    query = update.callback_query

    if query.data == 'menu':
        products = get_all_products(ACCESS_TOKEN)
        keyboard = [
            [
                InlineKeyboardButton(
                    product['name'],
                    callback_data=product['id'],
                )
                for product in products
            ],
            [InlineKeyboardButton('Cart', callback_data='cart')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        bot.send_message(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            text='Welcome! Please, choose a fish:',
        )

        return 'HANDLE_MENU'
    elif query.data == 'cart':
        generate_cart(bot, update)

        return 'HANDLE_CART'

    product_quantity, product_id = query.data.split(', ')
    add_product_to_cart(
        ACCESS_TOKEN,
        query.message.chat_id,
        product_id,
        int(product_quantity),
    )

    return 'HANDLE_MENU'


def handle_cart(bot, update):
    query = update.callback_query

    if query.data == 'menu':
        products = get_all_products(ACCESS_TOKEN)
        keyboard = [
            [
                InlineKeyboardButton(
                    product['name'],
                    callback_data=product['id'],
                )
                for product in products
            ],
            [InlineKeyboardButton('Cart', callback_data='cart')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        bot.send_message(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            text='Welcome! Please, choose a fish:',
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
        ACCESS_TOKEN,
        query.message.chat_id,
        query.data,
    )
    generate_cart(bot, update)

    return 'HANDLE_CART'


def handle_email(bot, update):
    email = update.message.text
    is_valid = validate_email(email)
    if is_valid:
        try:
            create_customer(ACCESS_TOKEN, str(update.message.chat_id), email)
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


def generate_cart(bot, update):
    query = update.callback_query
    cart_items = get_cart_items(ACCESS_TOKEN, query.message.chat_id)
    keyboard = [
        [
            InlineKeyboardButton(
                'Delete {0}'.format(cart_item['name']),
                callback_data=cart_item['id'],
            ),
        ]
        for cart_item in cart_items['data']
    ]
    keyboard.append(
        [
            InlineKeyboardButton('Menu', callback_data='menu'),
            InlineKeyboardButton('Pay', callback_data='pay'),
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not cart_items['data']:
        bot.send_message(
            text='Cart is empty',
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
        )
        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        return 'HANDLE_DESCRIPTION'

    total = cart_items['meta']['display_price']['without_tax']['formatted']
    cart_description = []
    for cart_item in cart_items['data']:
        name = cart_item['name']
        quantity = cart_item['quantity']
        price = cart_item['meta']['display_price']['with_tax']
        price_per_kg = price['unit']['formatted']
        total_price = price['value']['formatted']
        cart_description.append(
            '\nName: {0}\n\
            \nQuantity: {1}\
            \nPrice per kg: {2}\
            \nTotal product price: {3}\n\n'.format(
                name,
                quantity,
                price_per_kg,
                total_price,
            ),
        )

    cart_description.append('Total: {0}'.format(total))
    cart_recipe = ''.join(cart_description)
    bot.send_message(
        text=cart_recipe,
        reply_markup=reply_markup,
        chat_id=query.message.chat_id,
    )
    bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )


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
        user_state = db.get(chat_id).decode('utf-8')

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
        db.set(chat_id, next_state)
    except Exception as err:
        logger.error(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = REDIS_PASSWORD
        database_host = REDIS_HOST
        database_port = REDIS_PORT
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password
        )
    return _database


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    updater.start_polling()


if __name__ == '__main__':
    main()
