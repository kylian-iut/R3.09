import time
import threading

def task(i,vd):
    for k in range(vd,0,-1):
        print(f"thread {i} : {k}")
        time.sleep(1)

if __name__ == '__main__':
    t1 = threading.Thread(target=task, args=[1,5])
    t1.start()
    t2 = threading.Thread(target=task, args=[2,3])
    t2.start()
    t1.join()
    t2.join()
