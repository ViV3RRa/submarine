import sys
import boto3
import time
import json

dynamodb = boto3.resource('dynamodb')
receipt_table = dynamodb.Table('receipts')
products_table = dynamodb.Table('products')

INSERT = 'INSERT'

list_of_existing_eans = []
new_products = []


def get_all_products_from_dynamodb():
    print('Getting all existing products from table "products"')
    response = products_table.scan()
    
    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            print('Paginating the result set...')
            response = products_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
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
    
    receiptID = record['dynamodb']['Keys']['receiptID']['S']
    receipt = json.loads(get_receipt(receiptID))
    receiptLines = receipt['receiptLines']
    
    for line in receiptLines:
        productNumber = line['productNumber']
        productName = line['name']
        
        if productNumber is not None:
            if productNumber not in new_products and productNumber not in list_of_existing_eans:
                new_products.append(productNumber)
                add_product(productNumber, productName)
            else:
                print('Product with EAN: ' + productNumber + ' already registered...')
    return
    

def get_receipt(receiptID):
    print('Getting receipt with receiptID: ' + receiptID)
    response = receipt_table.get_item(
        Key={
            'receiptID': receiptID
        }
    )
    
    return response['Item']['receipt_json']
    

def add_product(ean, name):
    print('Inserting product with EAN: ' + str(ean) + ' and Name: ' + name + ' into table "products"')
    products_table.put_item(
            Item={
                'ean': ean,
                'insert_time': int(time.time() * 1000),
                'name': name,
                'tags': '{"tags": []}'
            }
        )
    

def lambda_handler(event, context):
    print('Updating list of products in table "products" at {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
    try:
        global list_of_existing_eans
        list_of_existing_eans = get_list_of_existing_eans()
        print('Currently ' + str(len(list_of_existing_eans)) + ' products in table "products"...')
        
        for record in event['Records']:
            print(str(record['eventName']) + ' receipt with receiptID: ' + record['dynamodb']['Keys']['receiptID']['S'])
            
            if record['eventName'] == INSERT:
                add_missing_products(record)
            else:
                print('Ignoring event ' + record['eventName'])
       
        print('Successfully processed %s records.' % str(len(event['Records'])))
        
    except:
        print("Failed updating products with error: " + str(sys.exc_info()))
        raise Exception('ERROR!!! Failed to update products!')
