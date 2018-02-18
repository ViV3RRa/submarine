import sys
import boto3
import time
import json

dynamodb = boto3.resource('dynamodb')
receipt_table = dynamodb.Table('receipts')
descriptions_table = dynamodb.Table('product_descriptions')

INSERT = 'INSERT'

list_of_existing_eans = []
new_products = []


def get_all_products_from_dynamodb():
    print('Getting all existing products from table "product_descriptions"')
    response = descriptions_table.scan()
    
    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            print('Paginating the result set...')
            response = descriptions_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items += response['Items']
        else:
            break
        
    return items
    

def get_list_of_existing_eans():
    print('Getting list of existing EAN\'s...')
    items = get_all_products_from_dynamodb()
    
    id_list = []
    for i in items:
        id_list.append(i['ean'])
        
    return id_list
    
    
def add_missing_products(record):
    global new_products
    
    receipt_id = record['dynamodb']['Keys']['receiptID']['S']
    receipt = json.loads(get_receipt(receipt_id))
    receipt_lines = receipt['receiptLines']
    
    for line in receipt_lines:
        product_number = line['productNumber']
        product_name = line['name']
        
        if product_number is not None:
            if product_number not in new_products and product_number not in list_of_existing_eans:
                new_products.append(product_number)
                add_product(product_number, product_name)
            else:
                print('Product with EAN: ' + product_number + ' already registered...')
    return
    

def get_receipt(receipt_id):
    print('Getting receipt with receiptID: ' + receipt_id)
    response = receipt_table.get_item(
        Key={
            'receiptID': receipt_id
        }
    )
    
    return response['Item']['receipt_json']
    

def add_product(ean, name):
    print('Inserting product with EAN: ' + str(ean) + ' and Name: ' + name + ' into table "product_descriptions"')
    descriptions_table.put_item(
            Item={
                'ean': ean,
                'insert_time': int(time.time() * 1000),
                'name': name,
                'tag': '-'
            }
        )
    

def lambda_handler(event, context):
    print('Updating list of products in table "product_descriptions" at {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
    try:
        global list_of_existing_eans
        list_of_existing_eans = get_list_of_existing_eans()
        print('Currently ' + str(len(list_of_existing_eans)) + ' products in table "product_descriptions"...')
        
        for record in event['Records']:
            print(str(record['eventName']) + ' receipt with receiptID: ' + record['dynamodb']['Keys']['receiptID']['S'])
            
            if record['eventName'] == INSERT:
                add_missing_products(record)
            else:
                print('Ignoring event ' + record['eventName'])
       
        print('Successfully processed %s records.' % str(len(event['Records'])))
        
    except:
        print("Failed updating product_descriptions with error: " + str(sys.exc_info()))
        raise Exception('ERROR!!! Failed to update product_descriptions!')
