import time
import requests
from multiprocessing import Process

STATUS_CODE_OK = 200
STATUS_CODE_FORBIDDEN = 403


def getAndAddReceipt(numCalls):
    for i in range(numCalls):
        requests.request("GET", "http://www.dr.dk/")

    return


def add_receipts(numProcesses, numCalls):

    # create a list to keep all processes
    processes = []

    # create a process per receipt
    count = 0
    while count < numProcesses:

        # create the process, pass instance and connection
        process = Process(target=getAndAddReceipt, args=(numCalls,))
        processes.append(process)
        count += 1

    # start all processes
    for process in processes:
        process.start()

    # make sure that all processes have finished
    for process in processes:
        process.join()

    return

_start = time.time()

#add_receipts(100, 1)
getAndAddReceipt(100)

print("Execution time: %s seconds" % (time.time() - _start))
