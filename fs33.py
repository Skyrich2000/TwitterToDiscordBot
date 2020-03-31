import numpy as np
import time
import asyncio
import threading
#np.save('usertable.npy', np.array({}),  allow_pickle=True, )
#a = np.load('usertable.npy', allow_pickle = True).tolist()
#print(len(a['1232324660282327040']['print']))
#a = time.strftime('%m/%d %H:%M:%S', time.localtime(time.time()))
#print(a)

def cor():
    a = "safd"
    try:
        try:
            raise Exception("asdfashdjkfasdklfjl")
        except Exception as e:
            raise Exception("asdfashdjkfasdklfj233333333l")
    except Exception as e:
        print(e)

async def acor():
    print("asdf aynce")
    loop2 = asyncio.get_event_loop()
    loop2.run_in_executor(None, cor)
    while True:
        pass

def th():
    asyncio.run(acor())

#threading.Thread(target=th).start()
#asyncio.run(acor())

cor()