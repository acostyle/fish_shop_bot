import math

from moltin import get_all_products
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_pagination(access_token, items_per_page):
    products = get_all_products(access_token)

    max_page = math.ceil(len(products) / items_per_page)

    start = 0
    end = items_per_page

    paginated_products = []
    for _ in range(max_page):
        paginated_products.append(products[start:end])
        start = end
        end += items_per_page
    
    return paginated_products


def create_menu_markup(access_token, page=0):
    products_per_page = 8
    products = get_pagination(access_token, products_per_page)
    
    keyboard = [
        [
            InlineKeyboardButton(
                '{0} 🐟'.format(product['name']),
                callback_data=product['id'],
            )
        ]
        for product in products[page]   
    ]

    if page == len(products) - 1:
        keyboard.append(
            [
                InlineKeyboardButton('⬅ Back', callback_data=f'page, {page - 1}'),
                InlineKeyboardButton('Cart 🛒', callback_data='cart'),
            ],
        )
    elif page == 0:
        keyboard.append(
            [
                InlineKeyboardButton('Cart 🛒', callback_data='cart'),
                InlineKeyboardButton('Forward ➡', callback_data=f'page, {page + 1}'),
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton('⬅ Back', callback_data=f'page, {page - 1}'),
                InlineKeyboardButton('Cart 🛒', callback_data='cart'),
                InlineKeyboardButton('Forward ➡', callback_data=f'page, {page + 1}'),
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup
