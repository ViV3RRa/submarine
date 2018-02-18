import time
import requests
from multiprocessing import Process


def run_sequential(numCalls):
    for i in range(numCalls):
        requests.request("GET", "http://www.dr.dk/")

    return


def run_with_multiple_processes(numProcesses, numCalls):

    # create a list to keep all processes
    processes = []

    # create a process per receipt
    count = 0
    while count < numProcesses:

        # create the process, pass instance and connection
        process = Process(target=run_sequential, args=(numCalls,))
        processes.append(process)
        count += 1

    # start all processes
    for process in processes:
        process.start()

    # make sure that all processes have finished
    for process in processes:
        process.join()

    return

def lambda_handler(event, context):
    try:

      _start = time.time()

      run_with_multiple_processes(1, 100)
      run_sequential(100)

      print("Execution time: %s seconds" % (time.time() - _start))
      
    except:
        print("Failed during test of multiprocessing with error:", sys.exc_info())
        raise
