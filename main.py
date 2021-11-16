import requests
from environs import Env

env = Env()
env.read_env()

API_BASE_URL = 'https://api.moltin.com'
CLIENT_ID = env.str('CLIENT_ID')


def get_access_token():
    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'implicit'
    }

    api_url = '{0}/oauth/access_token'.format(API_BASE_URL)
    response = requests.post(url=api_url, data=data)
    response.raise_for_status()

    return response.json()['access_token']


def main():
    access_token = get_access_token()


if __name__ == '__main__':
    main()

