import os
import sys
from pathlib import Path
import json

class Settings():
    
    def __init__(self):
        self.path = Path(os.getcwd()) / 'Files'
        self.loaded = False
        self.jsonsettings = ''
        if(not os.path.exists(self.path / 'settings.json')):
            self.create_settings()
            print('No settings files founded, creating one...')
        with open(self.path / 'settings.json') as f:
            self.jsonsettings = json.load(f)
            self.loaded = True         
    
    def create_settings(self):
        if(str(sys.platform).find('win') != -1):
            os.system("clr")
        else:
            os.system("clear")
        print("Please type in your settings:")
        results = {}
        results['settings'] = []
        print("To skip enter '*'") 
        result = input("Enter Twitch's bot name: ")
        results['settings'].append({'bot_username' : result})
        result = input("Enter Twitch's client id: ")
        results['settings'].append({'client_id' : result})
        result = input("Enter Twitch's token: ")
        results['settings'].append({'token' : result})
        result = input("Enter Sql's username: ")
        results['settings'].append({'sql_username' : result})
        result = input("Enter Sql's password: ")
        results['settings'].append({'sql_passwd' : result})
        result = input("Enter Sql's database name: ")
        results['settings'].append({'sql_db' : result})
        result = input("Choose session time (in minutes) per analysis: ")
        results['settings'].append({'session_time' : result})
        print("Enter favorite channels: (To finish send '*') ")
        cs = {}
        ch = ''
        i=1
        while(True):
            ch = input()
            if(ch == '*'):
                break
            cs[ch] = str(i)
            i += 1
        results['settings'].append({'channels' : cs})
        if(not self.loaded):
            with open(self.path / 'settings.json', 'w+') as outfile:  
                json.dump(results, outfile)
        else:
            i=0
            for e in results['settings']:
                key = list(e.keys())[0]
                if(key != 'channels'):
                    if(e[key] != '*'):
                        self.jsonsettings['settings'][i][key] = e[key]
                else:
                    for c,x in e['channels']:
                        if(self.channel_exist(c) == 0):
                            continue
                        self.jsonsettings['settings'][-1]['channels'].update({c:str(int(x)+len(self.get_favorites()))})
                    i+=1
                with open(self.path / 'settings.json', 'w') as outfile:  
                    json.dump(self.jsonsettings, outfile)
    
    def add_channels(self):
        if(not self.loaded):
            return 0
        cs = {}
        ch = ''
        i=1
        fav = self.get_favorites()
        fav_len = len(fav)
        print("Enter favorite channels: (To finish send '*') ")
        while(ch != '*'):
            ch = input()
            if(ch == '*'):
                break
            cs[ch] = str(i)
            i += 1
        for c,i in cs.items():
            if(self.channel_exist(c) == 0):
                continue
            self.jsonsettings['settings'][-1]['channels'].update({c:str(int(i)+fav_len)})
        with open(self.path / 'settings.json', 'w') as outfile:  
            json.dump(self.jsonsettings, outfile)
        return 1
    
    def remove_channel(self,channel):
        if(not self.loaded):
            return 0
        for c,i in self.jsonsettings['settings'][-1]['channels'].items():
            if(i == channel):
                del(self.jsonsettings['settings'][-1]['channels'][c])
                with open(self.path / 'settings.json', 'w') as outfile:  
                    json.dump(self.jsonsettings, outfile)
                print('Channel '+channel+' removed from favorites')
                return 1
        print('Channel is not in the favorites list')
        return 0
        
    def channel_exist(self,channel):
        if(not self.loaded):
            return 0
        if(channel in self.jsonsettings['settings'][-1]['channels']):
            return 0
        return 1
    
    def set_session_time(self, minutes):
        self.jsonsettings['settings'][6]['session_time'] = minutes
        with open(self.path / 'settings.json', 'w') as outfile:  
            json.dump(self.jsonsettings, outfile)
    
    def get_channel(self,index):
        for c,i in self.jsonsettings['settings'][-1]['channels'].items():
            if(i == index):
                return c
        return ''
    
    def get_favorites(self):
        return self.jsonsettings['settings'][-1]['channels']
    
    def get_botname(self):
        return self.jsonsettings['settings'][0]['bot_username']
    
    def get_clientid(self):
        return self.jsonsettings['settings'][1]['client_id']
    
    def get_token(self):
        return self.jsonsettings['settings'][2]['token']
    
    def get_sqlusername(self):
        return self.jsonsettings['settings'][3]['sql_username']
    
    def get_sqlpasswd(self):
        return self.jsonsettings['settings'][4]['sql_passwd']
    
    def get_sqldb(self):
        return self.jsonsettings['settings'][5]['sql_db']
    
    def get_session_time(self):
        return self.jsonsettings['settings'][6]['session_time']                     