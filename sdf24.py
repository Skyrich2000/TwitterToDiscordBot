import numpy as np
import time
import asyncio
import threading
import random
#np.save('usertable.npy', np.array({}),  allow_pickle=True)
#a = round(random.random()*1.5, 3)
#print(a)
#time.sleep(a)
#print("asdf")

print(np.load('usertable.npy', allow_pickle = True).tolist())