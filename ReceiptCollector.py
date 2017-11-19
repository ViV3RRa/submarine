import logging
import json
import StoreboxIntegration as Storebox

logger = logging.getLogger(__name__)


def get_receipts():
    logger.info('Getting receipts...')
    result = Storebox.get_data('https://dk.storebox.com/api/v1/receipts?count=999999999')

    if result.status_code != Storebox.STATUS_CODE_OK:
        logger.error('get_receipts() - Failed getting receipts with http status_code: %s', result.status_code)
        return

    data = json.loads(result.text)
    #for receipt in data['receipts']:
     #   get_receipt(receipt['receiptId'])

    print(result.text)
    #get_receipt(data['receipts'][0]['receiptId'])

    return


def get_receipt(receipt_id):
    logger.info('Getting receipt with receipt_id: %s', receipt_id)
    receipt = Storebox.get_data('https://dk.storebox.com/api/v1/receipts/' + receipt_id)

    if receipt.status_code != Storebox.STATUS_CODE_OK:
        logger.error('get_receipt() - Failed getting receiptID %s with http status_code: %s', receipt_id, receipt.status_code)
        return

    data = json.loads(receipt.text)
    print(data['receiptId'])
    print(receipt.text)

    return
