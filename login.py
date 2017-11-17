import requests
import json

url = "https://dk.storebox.com/api/v1/authenticate"

with open('config.json') as config_file:
	config_dict = json.load(config_file)


def get_data(url):
	cookies = {
		'auth-token': config_dict['auth-token']
	}
	print(cookies)
	r = requests.request("GET", url, cookies=cookies)

	print(r.status_code)
	if r.status_code != 200:
		update_auth_token()
		return get_data(url)
	
	else:
		return r


def update_auth_token():
	payload = "{\"username\":\"" + config_dict['username'] + "\",\"password\":\"" + config_dict['password'] + "\"}"
	headers = {
    	'content-type': "application/json"
	}

	response = requests.request("POST", url, data=payload, headers=headers)
	print(response.text)

	config_dict['auth-token'] = response.cookies['auth-token']
	update_config_file()

def update_user_credentials(username, password):
	config_dict[''] = username
	config_dict[''] = password
	update_config_file()


def update_config_file():
	with open('config.json', 'w') as f:
		f.write(json.dumps(config_dict))


def get_receipts():
	print(get_data('https://dk.storebox.com/api/v1/receipts').text)
	#print(get_number_of_receipts())
	return

def get_receipt():
	return

test = get_receipts()

#print(test.text)