from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from moltin import get_cart_items


def generate_cart(bot, update):
    query = update.callback_query
    cart_items = get_cart_items(query.message.chat_id)
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
            dedent('''\n
            Name: {0}
            
            Quantity: {1}
            Price per kg: {2}
            Total product price: {3}'''.format(
                name,
                quantity,
                price_per_kg,
                total_price,
            ),
            )
        )

    cart_description.append('\n\nTotal: {0}'.format(total))
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
