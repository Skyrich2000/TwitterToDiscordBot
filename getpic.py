from tweepy import API
from tweepy import Cursor
import twitter_credentials as auth
import numpy as np
import requests
import time
import asyncio
import random

LoadNum = int(requests.get("http://skyrich3.synology.me/~Huni/likesbot/loadnum.txt").text)
twitter_auth = API(auth.auth(), wait_on_rate_limit=True, timeout=10)
print_log = None

_errormap = ["", "마음", "트윗", "", "트윗중 사진"]
_titlemap = {'likes' : '이 누른 마음', 'tweets' : "의 트윗"}
_typemap = {'likes' : [0b000, 0b001], 'tweets' : [0b010, 0b110]}

class Twitter():
    def __init__(self, id="", screen_name=""):
        self.user_id = id
        if id == "":
            self.user_id = screen_name
        self.funmap = {'likes' : twitter_auth.favorites, 'tweets' : twitter_auth.user_timeline}

    def get_tweets(self, st): #예외 생성 - 마음 로딩 실패
        try:            
            arr = []
            time.sleep(round(random.random()*1.5, 3))
            for tweet in Cursor(self.funmap[st], id=self.user_id).items(LoadNum):
                arr.append(tweet._json)
            return arr
        except:
            raise Exception(f"Fail to load {st} {self.user_id}")

    def get_user(self): #예외 생성 - 계정 로딩 실패
        try:
            user = twitter_auth.get_user(id=self.user_id)._json
            return user['id_str'], user['name'], user['screen_name'], user['protected']
        except:
            raise Exception(f"{self.user_id} 는 존재하지 않는 아이디 입니다.")

class Data():
    def __init__(self):
        self.usertable = np.load('usertable.npy', allow_pickle = True).tolist()
        
        self.screen_nametable = {}
        for id in self.usertable:
            self.screen_nametable[self.usertable[id]['screen_name']] = id           
        pass

    def save(self):
        np.save('usertable.npy', np.array(self.usertable))
        pass

    def get_user_id(self, screen_name): #예외 생성 - 등록X 계정
        if screen_name in self.screen_nametable:
            return self.screen_nametable[screen_name]
        raise Exception(f"@{screen_name} 는 등록 되어있지 않은 계정입니다.")
        return f'[id of @{screen_name}]'
        pass

    def get_user_name(self, id="", screen_name=""): #예외 넘김 - 등록X 계정
        if id == "":
            id = self.get_user_id(screen_name)
        if id in self.usertable:
            return self.usertable[id]['name']
        return f'[name of {id}]'
        pass

    def get_user_screen_name(self, id): #예외 무시 - 아이디몰라
        if id in self.usertable:
            return self.usertable[id]['screen_name']
        return f'[screen name of {id}]'
        pass

    def get_user_protected(self, id): #예외 무시 - 보호몰라
        if id in self.usertable:
            return self.usertable[id]['protected']
        print_log(f"<span style='color:red'>System Error - Fail to load protected | {self.get_user_screen_name(id)}</span>")
        return True
        pass

    def update_user(self, id): #예외 넘김 - 
        s = time.time()
        print_log(f"System - Update user data : @{self.get_user_screen_name(id)}")
        _, self.usertable[id]['name'], self.usertable[id]['screen_name'], self.usertable[id]['protected'] = Twitter(id=id).get_user()
        self.screen_nametable[self.usertable[id]['screen_name']] = id
        self.save()
        print_log(f"System - {round(time.time() - s, 2)}sec | Update complete user @{self.usertable[id]['screen_name']}")
        pass

    def add_user(self, channel_id, screen_name): #예외 넘김
        if not screen_name in self.screen_nametable: #초기 등록
            s = time.time()
            print_log(f"System - Add new user @{screen_name} to {channel_id}")
            id, name, _, protected = Twitter(screen_name=screen_name).get_user()
            self.usertable[id] = {}
            self.usertable[id]['name'] = name
            self.usertable[id]['screen_name'] = screen_name
            self.usertable[id]['protected'] = protected
            self.usertable[id]['channel'] = {}
            self.usertable[id]['likes_history'] = []
            self.usertable[id]['tweets_history'] = []
            self.usertable[id]['print'] = []
            self.screen_nametable[screen_name] = id
            self.usertable[id]['type'] = [0, 0] #likes, tweets
            print_log(f"System - {round(time.time() - s, 2)}sec | Add complete new user @{screen_name}")
        _id = self.get_user_id(screen_name)
        if not channel_id in self.usertable[_id]['channel']:
            self.usertable[_id]['channel'][channel_id] = 0b000
        pass

    def add_history(self, id, tweetid, place):
        if not tweetid in self.usertable[id][place]:
            self.usertable[id][place].append(tweetid)
            if len(self.usertable[id][place]) > LoadNum * 2:
                self.usertable[id][place].pop(0)
            self.save()
            return True
        return False
        pass

    def add_print(self, id, data):
        self.usertable[id]['print'].append(data)
        pass

    def add_type(self, channel_id, id, newtype):
        #최소 갱신 필요시 true 반환
        before = self.usertable[id]['channel'][channel_id]
        if before & newtype:
            raise Exception(f"이미 채널에서 해당 계정의 {_errormap[newtype]}을 불러오고 있습니다.")
        if newtype == 0b001:
            self.usertable[id]['channel'][channel_id] = before | 0b001
            self.usertable[id]['type'][0] += 1
        else :
            self.usertable[id]['channel'][channel_id] = (before & 0b001) | newtype
            self.usertable[id]['type'][1] += not before & 0b110
        self.save()
        return self.usertable[id]['type'][newtype & 0b110 > 0] == 1
        pass

    def get_type(self, id, channel_id=None): #예외 해야됨
        if channel_id == None :
            return self.usertable[id]['type']
        return self.usertable[id]['channel'][channel_id]
        pass

    def get_channel_users(self, channel_id):
        users = []
        for id in self.usertable:
            if channel_id in self.usertable[id]['channel']:
                users.append(id)
        return users
        pass

    def del_channel_user(self, channel_id, id):#예외 생성 - 채널 등록X 계정
        if not channel_id in self.usertable[id]['channel']:
            raise Exception("이 채널에는 해당 계정이 등록 되어있지 않습니다.")
        if self.usertable[id]['channel'][channel_id] & 0b001:
            self.usertable[id]['type'][0] -= 1
        if self.usertable[id]['channel'][channel_id] & 0b110:
            self.usertable[id]['type'][1] -= 1
        del self.usertable[id]['channel'][channel_id]
        if len(self.usertable[id]['channel']) == 0:
            del self.screen_nametable[self.get_user_screen_name(id)]
            del self.usertable[id]
        self.save()
        pass

class Main():
    def __init__(self) :
        self.data = Data()

    def _list(self, channel_id): #예외 넘김 - 등록X 계정, 보호몰라
        st = ""
        st2 = ""
        users = self.data.get_channel_users(channel_id)
        for u in users:
            _t = self.data.get_user_name(id=u) + ' @' + self.data.get_user_screen_name(u)
            if self.data.get_user_protected(u): _t = "*" + _t + " - 보호된 계정*"
            if self.data.get_type(u, channel_id) & 0b001:
                st += _t + chr(10)
            elif self.data.get_type(u, channel_id) & 0b110:
                st2 += _t + chr(10)
        return st, st2
        pass

    def _add(self, channel_id, screen_name): #예외 넘김 - 계정 실패
        self.data.add_user(channel_id, screen_name)
        return self.data.get_user_name(screen_name=screen_name)

    def _add_type(self, channel_id, screen_name, newtype): #예외 넘김 - 등록X 계정
        return self.data.add_type(channel_id, self.data.get_user_id(screen_name), newtype)

    def _add_update_once(self, screen_name):
        _id = self.data.get_user_id(screen_name)
        try:
            if self.data.get_type(_id)[0]:
                self.update_history(_id, "likes")
            if self.data.get_type(_id)[1]:
                self.update_history(_id, "tweets")
        finally:
            self.data.usertable[_id]['print'] = []
        pass

    def _del(self, channel_id, screen_name): #예외 넘김 - 채널 등록X 계정
        self.data.del_channel_user(channel_id, self.data.get_user_id(screen_name))        
        pass

    def _clear(self, channel_id):
        users = self.data.get_channel_users(channel_id)
        for id in users:
            self._del(channel_id, self.data.get_user_screen_name(id))
        pass

    def _update(self, id="", screen_name=""): #예외 넘김 - 등록X 계정
        if id == "":
            id = self.data.get_user_id(screen_name)
        self.data.update_user(id)
        pass

    def update_history(self, id, st):#예외 넘김 - 보호몰라, 로딩 실패
        def append(value, state):
            if not 'media_url' in value:
                raise Exception(f'No media_url in media :  {value}')

            des = ""
            if st == "likes" : 
                des = state['user']['name'] + '  @'+state['user']['screen_name']

            adddes = ""
            if 'video_info' in value:
                for a in value['video_info']['variants']:
                    if 'bitrate' in a:
                        name = 'link'
                        if len(a["url"].split("/")) >= 7:
                            name = a["url"].split("/")[7]
                        adddes += f'[{name}]({a["url"]}) '
                    #self.data.add_print(id, {'type': _typemap[st][1], 'title': '', 'des': des, 'pic_url': '', 'url': ''})
            
            self.data.add_print(id, {'type': _typemap[st][1], 'title': f'{self.data.get_user_name(id=id)} 님{_titlemap[st]}',
                                     'des': des + adddes, 'pic_url': value['media_url'], 'url': value['display_url']})

        if not self.data.get_user_protected(id):
            for state in Twitter(id=id).get_tweets(st):
                if self.data.add_history(id, state['id_str'], st+"_history"):
                    self.data.add_print(id, {'type' : _typemap[st][0], 'title' : f'{self.data.get_user_name(id=id)} 님{_titlemap[st]}', 'des': state['text'], 'pic_url': '', 'url': ''})
                    if 'extended_entities' in state:
                        for value in state['extended_entities']['media']:
                            append(value, state)
                    elif 'media' in state['entities']:
                        for value in state['entities']['media']:
                            append(value, state)
