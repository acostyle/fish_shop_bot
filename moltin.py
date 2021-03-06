import json
import requests
from environs import Env

env = Env()
env.read_env()

API_BASE_URL = 'https://api.moltin.com'
CLIENT_ID = env.str('CLIENT_ID')
CLIENT_SECRET = env.str('CLIENT_SECRET')


def get_access_token(redis_db):
    access_token = redis_db.get('access_token')
    if not access_token:
        access_token, time_to_expire = get_auth_token()
        redis_db.set(
            'access_token',
            access_token,
            ex=time_to_expire,
        )

    return access_token


def get_auth_token():
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'implicit',
    }

    api_url = '{0}/oauth/access_token'.format(API_BASE_URL)
    response = requests.post(url=api_url, data=payload)
    response.raise_for_status()
    auth_data = response.json()

    return auth_data['access_token'], auth_data['expires_in']


def get_all_products(access_token):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'content-type': 'application/json',
    }
    api_url = '{0}/v2/products'.format(API_BASE_URL)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()
    products_data = response.json()

    products = [product for product in products_data['data']]

    return products


def get_product_by_id(access_token, product_id):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    api_url = '{0}/v2/products/{1}'.format(API_BASE_URL, product_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_product_photo_by_id(access_token, product_id):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    api_url = '{0}/v2/files/{1}'.format(API_BASE_URL, product_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()['data']['link']['href']


def get_or_create_cart(access_token, cart_id):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    api_url = '{0}/v2/carts/{1}'.format(API_BASE_URL, cart_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(access_token, cart_id, product_id, product_amount):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'content-type': 'application/json',
    }

    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': product_amount,
        },
    }

    api_url = '{0}/v2/carts/{1}/items'.format(API_BASE_URL, cart_id)
    response = requests.post(url=api_url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def get_cart_items(access_token, cart_id):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    api_url = '{0}/v2/carts/{1}/items'.format(API_BASE_URL, cart_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def delete_product_from_cart(access_token, cart_id, product_id):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    api_url = '{0}/v2/carts/{1}/items/{2}'.format(
        API_BASE_URL,
        cart_id,
        product_id,
    )
    response = requests.delete(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def create_customer(access_token, chat_id, email):
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    payload = {
        'data': {
            'type': 'customer',
            'name': chat_id,
            'email': email,
        },
    }
    api_url = '{0}/v2/customers/'.format(API_BASE_URL)
    response = requests.post(url=api_url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()['data']['id']
