import requests
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from textblob import TextBlob
import re
import pickle

address_ = 'https://twitchemotes.com/api_cache/v3/'
path = Path(os.getcwd()) / 'Files'

#pull twitch's emojis from API every 24hrs
def pull(package_):
    if(os.path.isfile(path / 'pull_date.txt')):
        with open(path / 'pull_date.txt','r') as f:
            pull_date = datetime.strptime(f.read().split('\n')[0],'%Y-%m-%d')
            if(pull_date < datetime.now() - timedelta(days=1)):
                get_data(package_)
                return 1
            else:
                print('pull data is up to date')
                return 0
    else:
        get_data(package_)
        return 1

#create a json file with emojis information
def get_data(package_):
    print('Downloading Emojis json file')
    j = json.dumps(requests.get(address_+package_+'.json').json())
    with open(path / str(package_+'.json'),'w+') as f:
        f.write(j)
        f.close()
    with open(path / 'pull_date.txt','w+') as f:
        f.write(str(datetime.now()).split('.')[0][0:10])
        f.close()
    print('done.')

#set sentiment to each emoji when determinable
def get_emojis():
    if(pull('subscriber') == 1):
        with open(path / 'subscriber.json','r') as f:
            j = json.load(f)
            subscriber_dict = {}
            r = re.compile('^[a-z-0-9]+')
            print('Creating Emojis-Sentiment dictionary, that might take a few minutes..')
            for key in j:
                i = 0
                #emojis emotion is divided to 4 sentiments with different score
                while(i < len(j[key]['emotes'])):
                    t = TextBlob(r.sub('',j[key]['emotes'][i]['code']))
                    if(t.sentiment.polarity == 0):
                        subscriber_dict[j[key]['emotes'][i]['code']] = ' '
                    elif(t.sentiment.polarity < 0.0):
                        subscriber_dict[j[key]['emotes'][i]['code']] = ':('
                    elif(t.sentiment.polarity > 0 and t.sentiment.polarity <= 0.5):
                        subscriber_dict[j[key]['emotes'][i]['code']] = ':)'
                    elif(t.sentiment.polarity > 0.5 and t.sentiment.polarity <= 0.75):
                        subscriber_dict[j[key]['emotes'][i]['code']] = ':P'
                    elif(t.sentiment.polarity > 0.75 and t.sentiment.polarity <= 1.0):
                        subscriber_dict[j[key]['emotes'][i]['code']] = ':D'
                    i += 1
        save_dict(subscriber_dict)
    else:
        print('emojis file already exist and up-to-date')

#create a pickle binary dictionary of emojis and their sentiment
#using pickle in-order to lower json file size from ~140Mb to 14Mb~ 
def save_dict(d):
    with open(path / 'subscriber_emojis.pkl','wb') as f:
        pickle.dump(d,f,pickle.HIGHEST_PROTOCOL)
    os.remove(path / 'subscriber.json')

#try to load dictionary , if there's an error re-create it
def load_dict():
    try:
        with open(path / 'subscriber_emojis.pkl','rb') as f:
            return pickle.load(f)
    except:
        os.remove(path / 'pull_date.txt')
        get_emojis()
        load_dict()