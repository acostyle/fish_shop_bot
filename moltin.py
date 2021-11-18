import datetime
import requests
from environs import Env

env = Env()
env.read_env()

API_BASE_URL = 'https://api.moltin.com'
CLIENT_ID = env.str('CLIENT_ID')
CLIENT_SECRET = env.str('CLIENT_SECRET')


def verify_token():
    token_data = get_auth_token()
    if is_token_valid(token_data):
        access_token = token_data[0]
    else:
        access_token = get_auth_token()[0]
    
    return access_token


def is_token_valid(token_data):
    token_expires = token_data[1]
    now = datetime.datetime.now()
    timestamp = datetime.datetime.fromtimestamp(token_expires)

    return timestamp > now


def get_auth_token():
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'implicit',
    }

    api_url = '{0}/oauth/access_token'.format(API_BASE_URL)
    response = requests.post(url=api_url, data=payload)
    response.raise_for_status()
    response_json = response.json()

    return response_json['access_token'], response_json['expires']


def get_all_products():
    access_token = verify_token()
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'content-type': 'application/json',
    }
    api_url = '{0}/v2/products'.format(API_BASE_URL)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()
    response_json = response.json()

    products = [product for product in response_json['data']]

    return products


def get_product_by_id(product_id):
    access_token = verify_token()
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    api_url = '{0}/v2/products/{1}'.format(API_BASE_URL, product_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_product_photo_by_id(product_id):
    access_token = verify_token()
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    api_url = '{0}/v2/files/{1}'.format(API_BASE_URL, product_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()['data']['link']['href']


def get_or_create_cart(cart_id):
    access_token = verify_token()
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    api_url = '{0}/v2/carts/{1}'.format(API_BASE_URL, cart_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(cart_id, product_id, product_amount):
    access_token = verify_token()
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


def get_cart_items(cart_id):
    access_token = verify_token()
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    api_url = '{0}/v2/carts/{1}/items'.format(API_BASE_URL, cart_id)
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def delete_product_from_cart(cart_id, product_id):
    access_token = verify_token()
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


def create_customer(chat_id, email):
    access_token = verify_token()
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
