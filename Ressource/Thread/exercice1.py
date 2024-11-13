import time
import threading

def task(i):
  for k in range(4):
    time.sleep(1)
    print(f"Je suis la thread {i}")

if __name__ == '__main__':
    t1 = threading.Thread(target=task, args=[1])
    t1.start()
    t2 = threading.Thread(target=task, args=[2])
    t2.start()
    t1.join()
    t2.join()