import discord
import getpic
import json
import numpy as np
import asyncio
import requests
import time
import threading
import os

class MyClient(discord.Client):
    async def on_ready(self):
        self.print_log('Bot - Logged on as ' + str(self.user))
        self.sys = getpic.Main()
        self.cycle = 1
        self.nameupdatetime = 0
        self.sleeptime = int(requests.get("http://skyrich3.synology.me/~Huni/likesbot/sleeptime.txt").text)/2
        self.print_log(f'Bot - Sleep time : {self.sleeptime} | Load num : {getpic.LoadNum}')
        self.loop.create_task(self.update())
        getpic.print_log = self.print_log
        await client.change_presence(activity=discord.Game("@help"))

    def print_log(self, log):
        def _func(log):
            tstr = time.strftime('%m/%d %H:%M:%S', time.localtime(time.time()))
            requests.get(f"http://skyrich3.synology.me/~Huni/likesbot/add.php?log={tstr}   {log}")
        self.loop.run_in_executor(None, _func, log)

    async def update(self):
        def send():
            for id in self.sys.data.usertable:
                embedlist = []
                for data in self.sys.data.usertable[id]['print']: #create embed
                    embed = discord.Embed(title=self.sys.data.get_user_name(id=id) + ' 님 께서 마음을 눌렀습니다.', description=data['pic_name'] + " " + data['pic_screen_name']) #color=0x00ff00)
                    embed.set_image(url=data['pic_url'])
                    embed.set_footer(text=data['url'])
                    embedlist.append(embed)
                self.sys.data.usertable[id]['print'] = [] #reset print
                for ch in self.sys.data.usertable[id]['channel']: #send embed           
                    for em in embedlist:
                        _ch = client.get_channel(int(ch))
                        if _ch == None: #if no channel
                            self.print_log(f"<span style='color:red'>Bot Send Error - {tstr} | Not Exist Channel {ch} | {self.sys.data.get_user_screen_name(id)}</span>")
                            self.sys._del(ch, id)
                        else :
                            yield _ch, em
            self.sys.data.save()
        await self.wait_until_ready()
        while not self.is_closed():
            tstr = f"{self.cycle} * {self.nameupdatetime}"
            #Request
            self.print_log(f"<b> Bot - {tstr} | Update {len(self.sys.data.usertable)} users history | Wait {self.sleeptime}sec </b>")
            th.ready_flag = True
            await asyncio.sleep(self.sleeptime)
            #Send Start
            s = time.time()
            for _ch, em in send():
                try: await _ch.send(embed=em)                                
                except Exception as e:
                    self.print_log(f"<span style='color:red'>Bot Send Error - {tstr} | {e} | {self.sys.data.get_user_screen_name(id)}</span>")
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
                st = '''트위터에서 마음찍은 사진들을 불러옵니다!
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
                embed = discord.Embed(title="계정 목록", description=self.sys._list(str(message.channel.id)))
                await message.channel.send(embed=embed)

            if message.content.startswith('@add'): #예외 - 등록X 계정, 이미 추가
                msg = message.content.split(" ")[1]
                self.loop.run_in_executor(None, self.sys._add, msg) # 한참 걸릴수있음
                await asyncio.sleep(2)
                try : uid = self.sys.data.get_user_id(msg)
                except: raise Exception(f"@{msg} 는 존재 하지 않는 계정 입니다.")
                self.sys.data.add_channel_user(str(message.channel.id), uid)
                embed = discord.Embed(description=self.sys.data.get_user_name(screen_name=msg) + " 추가 완료")
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@del'): #예외 - 등록X 계정 | 등록X 계정 , 채널 등록X 계정
                msg = message.content.split(" ")[1]
                embed = discord.Embed(description=self.sys.data.get_user_name(screen_name=msg) + " 제거 완료")
                self.sys._del(str(message.channel.id), msg)
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@update'): #예외 - 등록X 계정, 존재X 계정 | 등록X 계정
                msg = message.content.split(" ")[1]
                self.sys._update(screen_name=msg)
                embed = discord.Embed(description=f"{self.sys.data.get_user_name(screen_name=msg)} 의 계정 정보를 업데이트 했습니다.")
                await message.channel.send(embed=embed)

            if message.content == "@clear":
                self.sys._clear(str(message.channel.id))
                embed = discord.Embed(description="계정 목록 비움")
                await message.channel.send(embed=embed)
            
            if message.content.startswith('@debug'): #예외 - 등록X 계정, 
                msg = message.content.split(" ")[1]
                self.sleeptime = int(requests.get("http://skyrich3.synology.me/~Huni/likesbot/sleeptime.txt").text)/2
                await message.channel.send(json.dumps(self.sys.data.usertable[self.sys.data.get_user_id(msg)]))
        except Exception as e:
            embed = discord.Embed(description=str(e))
            embed.set_footer(text="Error message")
            await message.channel.send(embed=embed)

class MyThread():
    def __init__(self):
        self.ready_flag = False
        self.request_stack = []

    async def main(self):
        def cor(id, tstr):
            while self.ready_flag:
                pass
            self.request_stack.append(id)
            s = time.time()
            if client.nameupdatetime > 100:
                client.sys._update(id=id)
            client.sys.history_update(id)
            client.print_log(f"Thread - {tstr} ~ {client.nameupdatetime} | {round(time.time() - s, 2)}sec | @{client.sys.data.get_user_screen_name(id)} new uploaded {len(client.sys.data.usertable[id]['print'])}")
            while self.ready_flag:
                pass
            self.request_stack.remove(id)
        print("Thread - Thread Async Started!")
        thloop = asyncio.get_event_loop()
        while True:
            if self.ready_flag:
                client.print_log(f"Thread - {client.nameupdatetime} | Remain Stack {len(self.request_stack)} : {self.request_stack}")
                for id in client.sys.data.usertable:
                    if not id in self.request_stack:
                        thloop.run_in_executor(None, cor, id, client.nameupdatetime)
                self.ready_flag = False

    def run(self):
        asyncio.run(self.main())

client = MyClient()
th = MyThread()
threading.Thread(target=th.run).start()
client.run('NjgxOTA1NzQzODU4NzYxNzQ3.XlVQXQ.rSqAjGHzuenmG5a7ii5wUw5xW0o')


#TODO:
#지혼자 오류나면 재접하는데 그거때문에 업데이ㅡ 코루틴 2개 생긱ㅁ ㅠ