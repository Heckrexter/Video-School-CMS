import time

timea = time.time()
print(timea)
print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timea)))