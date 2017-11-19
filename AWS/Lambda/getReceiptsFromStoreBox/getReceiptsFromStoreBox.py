import sys
import boto3
import time
import requests
import json

dynamodb = boto3.resource('dynamodb')
receipt_table = dynamodb.Table('receipts')
config_table = dynamodb.Table('configuration')

STATUS_CODE_OK = 200
STATUS_CODE_FORBIDDEN = 403
config_dict = {}


def get_configuration():
    response = config_table.scan()
    global config_dict
    config_dict = response['Items'][0]
    return


def get_all_items_from_dynamodb():
    print('Getting all existing receipts from table "receipts"')
    response = receipt_table.scan()
    
    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            print('Paginating the result set...')
            response = receipt_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items += response['Items']
        else:
            break
        
    return items
    
def get_list_of_existing_ids():
    items = get_all_items_from_dynamodb()
    
    id_list = []
    for i in items:
        id_list.append(i['receiptID'])
        
    return id_list
    

def get_data(data_url):
    print('get_data() - Getting data from url: ' + data_url)
    cookies = {
        'auth-token': config_dict['authtoken']
    }

    r = requests.request("GET", data_url, cookies=cookies)

    if r.status_code != STATUS_CODE_OK:
        if r.status_code != STATUS_CODE_FORBIDDEN:
            return r
        else:
            print('get_data() - Failed with status_code: ' + str(r.status_code))
            update_auth_token()
            return get_data(data_url)

    else:
        return r
        

def update_auth_token():
    print('update_auth_token() - Updating auth_token...')
    global config_dict
    payload = "{\"username\":\"" + config_dict['username'] + "\",\"password\":\"" + config_dict['password'] + "\"}"
    headers = {
        'content-type': "application/json"
    }

    response = requests.request("POST", "https://dk.storebox.com/api/v1/authenticate", data=payload, headers=headers)
    print('update_auth_token() - status_code: ' + str(response.status_code))
    
    config_dict['authtoken'] = response.cookies['auth-token']
    print('update_auth_token() - Updated auth_token: ' + config_dict['authtoken'])
    update_configuration()
    
    
def update_configuration():
    config_table.update_item(
        Key={
            'username': config_dict['username']
        },
        UpdateExpression='SET authtoken = :val1',
        ExpressionAttributeValues={
            ':val1': config_dict['authtoken']
        }
    )
    
    
def get_receipt_ids(data):
    json_data = json.loads(data)
    
    receipts = []
    for receipt in json_data['receipts']:
        receipts.append(receipt['receiptId'])
        
    return receipts
    
    
def add_receipts(receipts_to_add):
    print('Adding ' + str(len(receipts_to_add)) + ' receipts to table "receipts"')
    
    for id in receipts_to_add:
        receipt_data = get_data('https://dk.storebox.com/api/v1/receipts/' + id)
        
        if receipt_data.status_code != STATUS_CODE_OK:
            print('Failed getting receipt for id ' + id + ' with status_code' + str(receipt_data.status_code))
            return
        
        receipt_table.put_item(
            Item={
                'receiptID': id,
                'insert_time': int(time.time() * 1000),
                'receipt_json': receipt_data.text
            }
        )
        
    return


def lambda_handler(event, context):
    print('Checking for new receipts at StoreBox at {}...'.format(event['time']))
    try:
        get_configuration()
        receipt_data = get_data('https://dk.storebox.com/api/v1/receipts?count=999999999')
        
        if receipt_data.status_code != STATUS_CODE_OK:
            raise Exception('Failed to get data from https://dk.storebox.com/api/v1/receipts?count=999999999 with status_code: ' + str(receipt_data.status_code))
        
        list_of_existing_ids = get_list_of_existing_ids()
        list_of_reseiptids = get_receipt_ids(receipt_data.text)
        
        receipts_to_add = []
        for i in list_of_reseiptids:
            if i not in list_of_existing_ids:
                receipts_to_add.append(i)
        
        print('Currently ' + str(len(list_of_existing_ids)) + ' receipts in table "receipts"...')
        
        if len(receipts_to_add) < 1:
            print('No receipts to add...')
        else:
            add_receipts(receipts_to_add)
        
    except:
        print("Failed getting receipts with error:", sys.exc_info())
        raise
