import sys
import boto3
import time
import calendar
import datetime as dt
import json
import uuid
from decimal import *

dynamodb = boto3.resource('dynamodb')
receipt_table = dynamodb.Table('receipts')
product_descriptions_table = dynamodb.Table('product_descriptions')
products_table = dynamodb.Table('products')

INSERT = 'INSERT'

product_descriptions = []


def get_product_descriptions():
    print('Getting all product_descriptions from table "product_descriptions"')
    response = product_descriptions_table.scan()
    
    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            print('Paginating the result set...')
            response = product_descriptions_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items += response['Items']
        else:
            break
        
    return items


def get_description(product_number):
    for description in product_descriptions:
        if description['ean'] == product_number:
            return description

    print('Description NOT found...')
    return None
    
    
def add_products(record):
    prev_product = None

    receipt_id = record['dynamodb']['Keys']['receiptID']['S']
    receipt = json.loads(get_receipt(receipt_id))
    receipt_lines = receipt['receiptLines']

    print('Inserting ' + str(len(receipt_lines)) + 'product(s) into table \'products\'')
    
    for line in receipt_lines:
        if line['name'].lower() == 'rabat' and prev_product is not None:
            prev_product['discount'] = True
            prev_product['discount_amount'] = line['totalPrice']['amount']

            put_product(prev_product)
            prev_product = None
            continue

        product_description = get_description(line['productNumber'])

        current_product = dict()
        current_product['uuid'] = uuid.uuid4().hex
        current_product['receipt_id'] = receipt['receiptId']
        current_product['insert_time'] = int(time.time() * 1000)
        current_product['purchase_time'] = get_timestamp(receipt['purchaseDate'])
        current_product['product_number'] = line['productNumber']
        current_product['product_name'] = line['name'] if product_description is None else product_description['name']
        current_product['tag'] = '-' if product_description is None else product_description['tag']
        current_product['count'] = line['count']
        current_product['item_price'] = line['itemPrice']['amount']
        current_product['total_price_without_discount'] = line['totalPrice']['amount']
        current_product['discount'] = False
        current_product['discount_amount'] = 0

        if prev_product is not None:
            put_product(prev_product)

        prev_product = current_product

    if prev_product is not None:
        put_product(prev_product)

    return
    

def get_timestamp(time_str):
    datetime_obj = dt.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S+%f')
    timestamp_in_seconds = calendar.timegm(datetime_obj.timetuple())

    return int(timestamp_in_seconds * 1000)


def get_receipt(receipt_id):
    print('Getting receipt with receipt_id: ' + receipt_id)
    response = receipt_table.get_item(
        Key={
            'receiptID': receipt_id
        }
    )
    
    return response['Item']['receipt_json']
    

def put_product(product):
    products_table.put_item(
            Item={
                'uuid': product['uuid'],
                'receipt_id': product['receipt_id'],
                'insert_time': product['insert_time'],
                'purchase_time': product['purchase_time'],
                'product_number': product['product_number'],
                'product_name': product['product_name'],
                'tag': product['tag'],
                'count': Decimal(str(product['count'])) ,
                'item_price': Decimal(str(product['item_price'])),
                'total_price_without_discount': Decimal(str(product['total_price_without_discount'])),
                'discount': product['discount'],
                'discount_amount': Decimal(str(product['discount_amount']))
            }
        )
    

def lambda_handler(event, context):
    print('Inserting products into table "products" at {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
    try:
        global product_descriptions
        product_descriptions = get_product_descriptions()
        
        for record in event['Records']:
            print(str(record['eventName']) + ' receipt with receiptID: ' + record['dynamodb']['Keys']['receiptID']['S'])
            
            if record['eventName'] == INSERT:
                add_products(record)
            else:
                print('Ignoring event ' + record['eventName'])
       
        print('Successfully processed %s records.' % str(len(event['Records'])))
        
    except:
        print("Failed updating products with error: " + str(sys.exc_info()))
        raise Exception('ERROR!!! Failed to update products!')
