import discord
import getpic
import json
import numpy as np
import asyncio
import requests
import time
import threading
import os

typemap = [0b001, 0b010, 0b100]
typemsg = ["님이 누른 마음중 미디어만 불러옵니다.", "님의 트윗을 불러옵니다.", "님의 트윗중 미디어만 불러옵니다."]

class MyClient(discord.Client):
    async def on_ready(self):
        print('Bot - Logged on as ' + str(self.user))
        self.cycle = 1
        self.nameupdatetime = 0
        self.sleeptime = int(requests.get("http://skyrich3.synology.me/~Huni/likesbot/sleeptime.txt").text)/2
        self.print_log(f'Bot - Sleep time : {self.sleeptime} | Load num : {getpic.LoadNum}')
        self.loop.create_task(self.update())
        getpic.print_log = self.print_log
        await client.change_presence(activity=discord.Game("@help"))

    def print_log(self, log):
        #print(log)
        def _func(log):
            tstr = time.strftime('%m/%d %H:%M:%S', time.localtime(time.time()))
            requests.get(f"http://skyrich3.synology.me/~Huni/likesbot/add.php?log={tstr}   {log}")
        self.loop.run_in_executor(None, _func, log)

    async def update(self):
        def send():
            for id in sys.data.usertable:
                errorlist = []
                embedlist = []
                for data in sys.data.usertable[id]['print']: #create embed
                    #embed = ''
                    #isem = False
                    #if data['title'] == '':
                    #    embed = data['des']
                    #    isem = False
                    #else :
                    embed = discord.Embed(title=data['title'], description=data['des']) #color=0x00ff00)
                    embed.set_image(url=data['pic_url'])
                    embed.set_footer(text=data['url'])
                    #    isem = True
                    embedlist.append([data['type'], embed]) #, isem])
                sys.data.usertable[id]['print'] = []

                for ch in sys.data.usertable[id]['channel']: #send embed
                    _ch = client.get_channel(int(ch))
                    if _ch == None: #if no channel
                        self.print_log(f"<span style='color:red'>Bot Send Error - {tstr} | Not Exist Channel {ch} | {sys.data.get_user_screen_name(id)}</span>")
                        errorlist.append([ch, sys.data.get_user_screen_name(id)])
                    else :
                        for em in embedlist:
                            if sys.data.get_type(id, ch) & em[0]:
                                yield _ch, em[1] #, em[2]
                for d in errorlist:
                    sys._del(d[0], d[1])

            sys.data.save()
        await self.wait_until_ready()
        while not self.is_closed():
            tstr = f"{self.cycle} * {self.nameupdatetime}"
            #Request
            self.print_log(f"<b> Bot - {tstr} | Update {len(sys.data.usertable)} users history | Wait {self.sleeptime}sec </b>")
            th.ready_flag = True
            await asyncio.sleep(self.sleeptime)
            #Send Start
            s = time.time()
            try:
                for _ch, em in send():
                    await _ch.send(embed=em)
                    #if isem : await _ch.send(embed=em)
                    #else : await _ch.send(em)
            except Exception as e:
                self.print_log(f"<span style='color:red'>Bot Send Error - {tstr} | {e} | {sys.data.get_user_screen_name(id)}</span>")
            temp = os.popen("vcgencmd measure_temp").readline().replace("temp=","").replace('\n',"")
            self.print_log(f"<b>Bot - {tstr} | {round(time.time() - s, 2)}sec | Cpu {temp} | Send end | Wait {self.sleeptime}sec</b>")
            #Cycle
            if self.nameupdatetime > 100 :
                self.nameupdatetime = 0
                self.cycle += 1
            self.nameupdatetime += 1
            await asyncio.sleep(self.sleeptime)
        self.print_log("<span style='color:red'>Bot Error - Bot Closed!!</span>")

    async def on_message(self, message):
        if message.author == self.user: # don't respond to ourselves
            return

        try : 
            if message.content == "@help":
                st = '''트윗들을 불러옵니다!
                @list : 계정 목록 확인
                @add 트위터 아이디 : 트위터 계정 추가
                @del 트위터 아이디 : 트위터 계정 제거
                @update 트위터 아이디 : 트위터 계정 정보 업데이트
                @clear : 계정 목록 전체 제거
                @link : 봇 초대 링크'''
                embed = discord.Embed(title="도움말", description=st)
                await message.channel.send(embed=embed)
            
            if message.content == "@link":
                await message.channel.send("https://discordapp.com/oauth2/authorize?client_id=681905743858761747&scope=bot")

            if message.content == '@list':
                des, des2 = sys._list(str(message.channel.id))
                if des != "":
                    embed = discord.Embed(title="마음 계정 목록", description=des)
                    await message.channel.send(embed=embed)
                if des2 != "":
                    embed = discord.Embed(title="트윗 계정 목록", description=des2)
                    await message.channel.send(embed=embed)
                elif des == "":
                    embed = discord.Embed(description="등록된 계정이 없습니다.")
                    await message.channel.send(embed=embed)

            if th.ready_flag:
                await asyncio.sleep(0.2)

            if message.content.startswith('@add'): #예외 - 등록X 계정, 이미 추가
                msg = message.content.split(" ")[1]
                name = sys._add(str(message.channel.id), msg)
                des = """1 - 마음중 미디어를 불러옵니다.
                2 - 트윗을 불러옵니다.
                3 - 트윗중 미디어만 불러옵니다."""
                embed = discord.Embed(title=f"{name} 님의 무엇을 불러오시겠어요?", description=des)
                await message.channel.send(embed=embed)

                def check(ms):
                    if ms.channel == message.channel and ms.author == message.author:
                        if ms.content in ['1', '2', '3']:
                            return True
                    return False
                
                try:
                    reaction = await client.wait_for('message', timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    sys._del(str(message.channel.id), msg)
                    raise Exception(f"제대로 선택하지 않아 {name} 님 추가를 취소 합니다.")

                idx = int(reaction.content)-1
                des = f"앞으로 {name} {typemsg[idx]}"
                if sys._add_type(str(message.channel.id), msg, typemap[idx]):
                    self.loop.run_in_executor(None, sys._add_update_once, msg)

                embed = discord.Embed(description=des)
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@del'): #예외 - 등록X 계정 , 채널 등록X 계정
                msg = message.content.split(" ")[1]
                embed = discord.Embed(description=sys.data.get_user_name(screen_name=msg) + " 님을 더이상 불러오지 않습니다.")
                sys._del(str(message.channel.id), msg)
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@update'): #예외 - 등록X 계정, 계정 로딩 실패
                msg = message.content.split(" ")[1]
                sys._update(screen_name=msg)
                embed = discord.Embed(description=f"{sys.data.get_user_name(screen_name=msg)} 님의 계정 정보를 업데이트 했습니다.")
                await message.channel.send(embed=embed)

            if message.content == "@clear":
                sys._clear(str(message.channel.id))
                embed = discord.Embed(description="더이상 아무도 불러오지 않습니다.")
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@debug'): #예외 - 등록X 계정,
                msg = message.content.split(" ")[1]
                self.sleeptime = int(requests.get("http://skyrich3.synology.me/~Huni/likesbot/sleeptime.txt").text)/2
                await message.channel.send(sys.data.get_user_id(msg) + " : " + json.dumps(sys.data.usertable[sys.data.get_user_id(msg)]))
        except Exception as e:
            embed = discord.Embed(description=str(e))
            embed.set_footer(text="Error message")
            await message.channel.send(embed=embed)

class MyThread():
    def __init__(self):
        self.ready_flag = False
        self.request_stack = []

    async def main(self):
        def _cor(id, rqid, tstr, st):
            while self.ready_flag:
                pass
            self.request_stack.append(rqid)
            try:
                s = time.time()
                sys.update_history(id, st)
                client.print_log(f"Thread - {tstr} ~ {client.nameupdatetime} | {round(time.time() - s, 2)}sec | @{sys.data.get_user_screen_name(id)} new uploaded {len(sys.data.usertable[id]['print'])} {st}")
            except Exception as e:
                client.print_log(f"<span style='color:red'>System Update {st} Error - {e} | {id}</span>")
            finally:
                while self.ready_flag:
                    pass
                self.request_stack.remove(rqid)
        print("Thread - Thread Async Started!")
        thloop = asyncio.get_event_loop()
        while True:
            if self.ready_flag:
                client.print_log(f"Thread - {client.nameupdatetime} | Remain Stack {len(self.request_stack)} : {self.request_stack}")
                for id in sys.data.usertable:
                    if sys.data.get_type(id)[0]:
                        rqid = "L" + id
                        if not rqid in self.request_stack:
                            thloop.run_in_executor(None, _cor, id, rqid ,client.nameupdatetime, "likes")
                    if sys.data.get_type(id)[1]:
                        rqid = "T" + id
                        if not rqid in self.request_stack:
                            thloop.run_in_executor(None, _cor, id, rqid ,client.nameupdatetime, "tweets")
                    if client.nameupdatetime > 100:
                        thloop.run_in_executor(None, sys._update, id)
                self.ready_flag = False

    def run(self):
        asyncio.run(self.main())

sys = getpic.Main()
client = MyClient()
th = MyThread()
threading.Thread(target=th.run).start()
client.run('NjgxOTA1NzQzODU4NzYxNzQ3.XlVQXQ.rSqAjGHzuenmG5a7ii5wUw5xW0o')
