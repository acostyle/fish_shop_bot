import requests
from environs import Env
from pprint import pprint
env = Env()
env.read_env()

API_BASE_URL = 'https://api.moltin.com'
CLIENT_ID = env.str('CLIENT_ID')
CLIENT_SECRET = env.str('CLIENT_SECRET')


def get_auth_token():
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'implicit'
    }

    api_url = '{0}/oauth/access_token'.format(API_BASE_URL)
    response = requests.post(url=api_url, data=data)
    response.raise_for_status()
    response_json = response.json()

    return response_json['access_token']


def get_all_products(access_token):
    api_url = '{0}/v2/products'.format(API_BASE_URL)
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'content-type': 'application/json',
    }
    response = requests.get(url=api_url, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    access_token = get_auth_token()
    all_products = get_all_products(access_token)
    pprint(all_products)


if __name__ == '__main__':
    main()

