import requests
import asyncio
import time
import random

async def a(msg): # api
    print("async ", msg)
    pass

async def lazy_greet(msg): #내가 만든거
    print('start ', msg)
    for _ in range(random.randint(1,50)):
        requests.get("http://naver.com").text[:4]
    print('end ', msg)
    await a(msg) 
    print('asyncio end', msg)

async def main():
    messages = 'hello world apple banana cherry'.split()
    cos = [lazy_greet(m) for m in messages]
    (done, pending) = await asyncio.wait(cos, timeout=5)
    if pending:
        print("there is {} tasks not completed".format(len(pending)))
        for f in pending:
            f.cancel()
    for f in done:
        print(await f)
    #for m in messages:
        #loop.run_in_executor(None, lazy_greet, m)
    print("next")

loop = asyncio.get_event_loop()  # 이벤트 루프를 얻음
asyncio.run(main())  # main이 끝날 때까지 기다림
#loop.close()