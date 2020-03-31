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

class Twitter():
    def __init__(self, id="", screen_name=""):
        self.user_id = id
        if id == "":
            self.user_id = screen_name

    def get_favorites(self): #예외 생성 - 마음 로딩 실패
        try:
            favorites_tweets = []
            time.sleep(round(random.random()*1.5, 3))
            for tweet in Cursor(twitter_auth.favorites, id=self.user_id).items(LoadNum):
                favorites_tweets.append(tweet._json)
            return favorites_tweets
        except:
            raise Exception(f"Fail to load tweets {self.user_id}")

    def get_user(self): #예외 생성 - 존재X 계정
        try:
            user = twitter_auth.get_user(id=self.user_id)._json
            return user['id_str'], user['name'], user['screen_name'], user['protected']
        except:
            raise Exception(f"계정 {self.user_id} 을 불러오는데 실패했습니다.")

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

    def add_user(self, screen_name): #예외 넘김
        s = time.time()
        print_log(f"System - Add new user @{screen_name}")
        id, name, _, protected = Twitter(screen_name=screen_name).get_user()
        self.usertable[id] = {}
        self.usertable[id]['name'] = name
        self.usertable[id]['screen_name'] = screen_name
        self.usertable[id]['protected'] = protected
        self.usertable[id]['channel'] = []
        self.usertable[id]['history'] = []
        self.usertable[id]['print'] = []
        self.screen_nametable[screen_name] = id
        print_log(f"System - {round(time.time() - s, 2)}sec | Add complete new user @{screen_name}")
        pass

    def add_history(self, id, data):
        if not data['pic_url'] in self.usertable[id]['history']:
            self.usertable[id]['history'].append(data['pic_url'])
            self.usertable[id]['print'].append(data)
            if len(self.usertable[id]['history']) > LoadNum * 6:
                self.usertable[id]['history'].pop(0)
            self.save()
        pass

    def get_channel_users(self, channel_id):
        users = []
        for id in self.usertable:
            if channel_id in self.usertable[id]['channel']:
                users.append(id)
        return users
        pass

    def add_channel_user(self, channel_id, id):#예외 생성 - 이미 추가
        if channel_id in self.usertable[id]['channel']:
            raise Exception("이미 채널에 해당 계정이 추가 되어 있습니다.")
        self.usertable[id]['channel'].append(channel_id)
        self.save()
        pass

    def del_channel_user(self, channel_id, id):#예외 생성 - 채널 등록X 계정
        if not channel_id in self.usertable[id]['channel']:
            raise Exception("이 채널에는 해당 계정이 등록 되어있지 않습니다.")
        self.usertable[id]['channel'].remove(channel_id)
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
        users = self.data.get_channel_users(channel_id)
        for u in users:
            n = self.data.get_user_name(id=u) + ' @' + self.data.get_user_screen_name(u)
            if self.data.get_user_protected(u):
                st += "*" + n + " - 보호된 계정*"
            else :
                st += n
            st += chr(10)
        return st
        pass

    def _add(self, screen_name): #예외 안넘김
        if not screen_name in self.data.screen_nametable:
            try: self.data.add_user(screen_name)
            except Exception: return
            self.history_update(self.data.get_user_id(screen_name))
            self.data.usertable[self.data.get_user_id(screen_name)]['print'] = []        

    def _del(self, channel_id, screen_name): #예외 넘김 - 등록X 계정 , 채널 등록X 계정
        self.data.del_channel_user(channel_id, self.data.get_user_id(screen_name))        
        pass

    def _clear(self, channel_id):
        users = self.data.get_channel_users(channel_id)
        for id in users:
            self._del(channel_id, self.data.get_user_screen_name(id))
        pass

    def _update(self, screen_name="", id=""): #예외 넘김 - 등록X 계정
        if id == "":
            id = self.data.get_user_id(screen_name)
        self.data.update_user(id)
        pass

    def history_update(self, id):#예외 처리 - 보호몰라, 마음 로딩 실패
        def append(value, state):
            if not 'media_url' in value:
                raise Exception(f'No media_url in media :  {value}')
            self.data.add_history(id, {'pic_name': state['user']['name'], 'pic_screen_name' : '@'+state['user']['screen_name'], 'pic_url': value['media_url'], 'url': value['display_url']})

        try :
            if not self.data.get_user_protected(id):
                for state in Twitter(id=id).get_favorites():
                    if 'extended_entities' in state:
                        for value in state['extended_entities']['media']:
                            append(value, state)
                    elif 'media' in state['entities']:
                        for value in state['entities']['media']:
                            append(value, state)
        except Exception as e:
            print_log(f"<span style='color:red'>System Update Error - {e} | {self.data.get_user_screen_name(id)}</span>")
            self._update(id=id)