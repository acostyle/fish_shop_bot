import requests
from environs import Env

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

    return response_json['access_token'], response_json['expires']


def main():
    access_token = get_auth_token()
    print(access_token)


if __name__ == '__main__':
    main()

