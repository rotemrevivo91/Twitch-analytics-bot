#Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#   http://aws.amazon.com/apache2.0/
#or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import os
import irc.bot
import requests
import datetime
from time import time,sleep
import pandas as pd
from pathlib import Path
import sys
import signal
import threading

from text_processing import TextProcessing
from text_analyzing import TextAnalyzing
from graph import Graph

class TwitchBot(irc.bot.SingleServerIRCBot):
    
    channel_id = ''
    messageCount = 0
    filesCounter = 0
    df = pd.DataFrame()
    path = Path(os.getcwd())
    
    def __init__(self, username, client_id, token, channel, d, s, session_time):
        #start time
        self.it = time()
        #set session time in seconds
        self.session_time = session_time
        #connection details
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        #get processed emoji dictionary
        nd = {}
        for k in d:
            nd[k.casefold()] = d[k]
        self.d = nd
        #sql
        self.s = s
        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        try:
            r = requests.get(url, headers=headers).json()
        except:
            print('No internet connection..Please connect to the internet and try again..')
            sys.exit()
        try:
            self.channel_id = r['users'][0]['_id']
        except:
            print('No such channel exist. Please try a different channel.')
            sys.exit()
        
        #check if stream is alive
        if(self.is_streamlive()):
            print('Channel is live..strating chat stream')
        else:
            print('Channel is not currently live. Please try a different channel.')
            sys.exit()
		
        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        try:
            irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        except:
            print("Can't connect to IRC server, please try again.")
            sys.exit()

        #update channel_name:channel_id dictionary
        chd = self.channel_id+':'+channel
        update = True
        if(os.path.exists(self.path / 'Files/channels_dict.txt')):
            with open(self.path / 'Files/channels_dict.txt','r+') as f:
                d = f.read().split('\n')
                for line in d:
                    if self.channel_id in line.split(':'):
                        update = False
                        break
                if(update):
                    f.write(chd+'\n')
        else:
            with open(self.path / 'Files/channels_dict.txt','a+') as f:
                f.write(chd+'\n')
        update = True
        #update bots file
        with open(self.path / 'Files/bots.txt','r+') as f:
            d = f.read().split('\n')
            for line in d:
                if channel+'bot' in line:
                    update = False
            if(update):
                f.write(channel+'bot\n')
        self.name = self.name_distributer()
        self.t = TextProcessing()
        #capture ctrl+c for graceful shutdown: in-order to save progress and performing analysis if possible
        signal.signal(signal.SIGINT, self.signal_handler)
        self.sig = True
        #open a thread to check stream's status
        threading.Thread(target=self.check_stream).start()
    
    #capture ctrl+c for graceful shutdown
    def signal_handler(self, sig, frame):
        self.sig = False
        self.create_csv('', '', '', True)
        print('All progress saved. Exiting.')
        sys.exit(0)
    
    #check stream status every 10s, if stream has ended graceful shutdown
    def check_stream(self):
        while(self.sig):
            if(self.is_streamlive()):
                sleep(10)
            else:
                print('Stream has ended. Saving progress.')
                self.signal_handler('','')
       
    def is_streamlive(self):
        #check if stream is alive
        url = 'https://api.twitch.tv/helix/streams?user_id=' + self.channel_id
        headers = {'Client-ID': self.client_id}
        try:
            r = requests.get(url, headers=headers).json()
            if(r['data'][0]['type'] == 'live'):
                return True
            else:
                return False
        except:
            return False
            
    def on_welcome(self, c, e):
        print ('Joining ' + self.channel)
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    #incoming messages are saved to a csv file
    #Format: nickname,message,datetime (year-month-day hour:minute:second)
    def on_pubmsg(self, c, e):
        #ignore command messages
        if e.arguments[0][:1] != '!' and len(e.arguments[0]) > 1:
            message = self.t.process_message(str(e.arguments[0]), str(e.source.nick),self.d)
            if(message != False):
                print(e.source.nick+': '+message)
                dt = str(datetime.datetime.now()).split('.')[0]
                self.create_csv(str(e.source.nick),str(message),dt,False)
        return
    
    #set a name to each new csv file depending on channel name and number of previously created files f the channel
    def name_distributer(self):
        if(not os.path.exists(self.path / 'Channels')):
            os.mkdir(self.path / 'Channels')
        dr = os.listdir(self.path / 'Channels/')
        if self.get_channel_name() not in dr:
            os.mkdir(self.path / 'Channels' / self.get_channel_name())
        if(not os.path.exists(self.path / 'Channels' / self.get_channel_name() / 'Data')):
            os.mkdir(self.path / 'Channels' / self.get_channel_name() / 'Data')
        dr = os.listdir(self.path / 'Channels' / self.get_channel_name() / 'Data')
        revision = len(dr) + 1
        return self.get_channel_name()+'_'+str(revision)
    
    #appending each new incoming message to a dataframe
    #every 1000 messages save a csv file
    #!user could choose how often to save a csv file (time based rather than messages as messages traffic vary from channel to channel)      
    def create_csv(self, nick, message, mytimestamp, stop):
        if(not stop):
            self.messageCount += 1
            self.df = self.df.append([[nick,message,mytimestamp]],ignore_index=True)
        if(float(time()-self.it) >= float(int(self.session_time)*60) or stop):
            if(self.messageCount > 0):
                self.messageCount = 0
                self.filesCounter += 1
                self.df.columns=['Nick','Message','Timestamp']
                self.df.to_csv(self.path / 'Channels' / self.get_channel_name() / 'Data' / str(self.name+'.csv'),index=False,encoding='utf-8',sep=',')
                self.df = pd.DataFrame()
                #start analyzing data
                sleep(2)
                TextAnalyzing(self.channel_id,self.get_channel_name(),self.name.split('_')[1],self.s)
                try:
                    g = Graph(self.channel_id,self.get_channel_name(),self.name.split('_')[1],self.s)
                    g.graph1()
                    g.graph2()
                    g.graph3()
                    g.graph4()
                except:
                    print('Data set too small to plot as grpahs')
                self.it = time()
                self.name = self.name_distributer()
    
    def get_channel_id(self):
        return self.channel_id
    
    def get_channel_name(self):
        return self.channel.split('#')[1]