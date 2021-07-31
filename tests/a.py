from b import run_api
from threading import Thread
from time import sleep

def func(data):
    for _ in range(100):
        sleep(5)
        data['n'] += 1

data = {'n': 1}
func_run = Thread(target=func, args=[data])
func_run.start()
run_api(data)
func_run.join()