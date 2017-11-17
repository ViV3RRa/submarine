import json


def get_receipts():
    print(get_data('https://dk.storebox.com/api/v1/receipts').text)
    # print(get_number_of_receipts())
    return


def get_receipt():
    return


get_receipts()

# print(test.text)
