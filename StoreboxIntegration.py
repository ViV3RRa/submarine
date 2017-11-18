import logging
import requests
import json

logger = logging.getLogger(__name__)

STATUS_CODE_OK = 200
STATUS_CODE_FORBIDDEN = 403

url = "https://dk.storebox.com/api/v1/authenticate"

with open('config.json') as config_file:
    logger.info('Loading configuration...')
    config_dict = json.load(config_file)


def get_data(data_url):
    logger.info('get_data() - Getting data from url: %s', data_url)
    logger.info('get_data() - Using auth_token: %s', config_dict['auth-token'])
    cookies = {
        'auth-token': config_dict['auth-token']
    }

    r = requests.request("GET", data_url, cookies=cookies)

    if r.status_code != STATUS_CODE_OK:
        if r.status_code != STATUS_CODE_FORBIDDEN:
            return r
        else:
            logger.warning('get_data() - Failed status_code: %s', r.status_code)
            update_auth_token()
            return get_data(data_url)

    else:
        return r


def update_auth_token():
    logger.info('update_auth_token() - Updating auth_token...')
    payload = "{\"username\":\"" + config_dict['username'] + "\",\"password\":\"" + config_dict['password'] + "\"}"
    headers = {
        'content-type': "application/json"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    config_dict['auth-token'] = response.cookies['auth-token']
    logger.info('update_auth_token() - Updated auth_token: %s', config_dict['auth-token'])
    update_config_file()


def update_user_credentials(username, password):
    logger.info('update_user_credentials() - Updating user credentials...')
    config_dict[''] = username
    config_dict[''] = password
    update_config_file()


def update_config_file():
    logger.info('Updating configuration...')
    with open('config.json', 'w') as f:
        f.write(json.dumps(config_dict))
