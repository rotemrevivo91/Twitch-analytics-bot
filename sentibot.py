#Solve an issue with anaconda environment and Windows where capturing ctrl+c to save progress and exit is not
#captured and instead FORTAN compiler throws an forrtl error (200) and crashed python.
import os
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

import sys
from settings import Settings
from sql import Sql
import re
from pathlib import Path

#download nltk files for NLP if not existent
import nltk
try:
    nltk.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

#global path
path = Path(os.getcwd())

def main(): 
    sett = Settings()
    s = Sql(sett.get_sqldb(), sett.get_sqlusername(), sett.get_sqlpasswd())
    subject = ''
    channel = ''
    start = False
    #find os
    if(str(sys.platform).find('win') != -1):
        cm = 'cls'
    else:
        cm = 'clear'
        
    #User API
    if(len(sys.argv) < 2):
        print('Wrong input for help use: sentibot -h')
        sys.exit()
        
    #help                                                                   #
    if(sys.argv[1] == '-h'):
        os.system(cm)
        print('')
        print('###################################################################################################################################')
        print('#                                                        SentiBot v1.0                                                            #')
        print('#                                                                                                                                 #')
        print('# python sentibot <channel_name> [context] - joins a channel                                                                      #')
        print('# python sentibot -f <channel_number> [context] - chooses a channel from favorites list to join to                                #')
        print('# python sentibot -sf - shows all favorite channels                                                                               #')
        print('# python sentibot -rf <channel_number> - removes a favorite channel from the list                                                 #')
        print('# python sentibot -af - opens a menu to add new favorites channels                                                                #')
        print('# python sentibot -st <time_minutes> - change session time per analysis                                                           #')
        print('# python sentibot -s - opens the settings menu for update                                                                         #')
        print('# python sentibot -ss - show all settings                                                                                         #')
        print('# python sentibot -a <channel_name> <1-n> - analyze data files of a channel                                                       #')
        print('#                                                                                                                                 #')
        print('# *   <> - obligatory field , [] - optional field                                                                                 #')
        print('# **  Exit and save csv file and potential analyze (if data set not too small): ctrl+c                                            #')
        print('# *** optional context will download a file for text analysis. context could be name of a game/show showed in the channel.        #\n'+
              '#     When not mentioned a default context file will be used for analyzing the data. context should be captioned in [] and could  #\n'+
              '#     contain multiple words separated by an underscore (Ex: python sentibot examplechannel [dr._who])                            #')
        print('###################################################################################################################################')
        print('')
    #favorites
    elif(sys.argv[1] == '-f'):
        try:
            channel = sett.get_channel(sys.argv[2])
            if(channel == ''):
                print('No such channel in your favorite list.')
                sys.exit()
        except:
            print("Please enter a number after -f")
            sys.exit()
        try:
            subject = re.sub('[][]','',sys.argv[3])
        except:
            subject = ''
        start = True
    #show favorites
    elif(sys.argv[1] == '-sf'):
        print(sett.get_favorites())
    #remove from favorites
    elif(sys.argv[1] == '-rf'):
        try:
            channel_num = sys.argv[2]
        except:
            print("Please enter a number after -rf")
            sys.exit()
        sett.remove_channel(channel_num)
    #add favorites
    elif(sys.argv[1] == '-af'):
        sett.add_channels()
    #edit session time
    elif(sys.argv[1] == '-st'):
        try:
            minutes = sys.argv[2]
        except:
            print('Please enter a number after -st')
            sys.exit()
        sett.set_session_time(minutes)
    #settings
    elif(sys.argv[1] == '-s'):
        sett.create_settings()
    #show all settings
    elif(sys.argv[1] == '-ss'):
        answer = input("You're about to view sensitive information. Do you wish to continue? Y/N: ")
        if(answer == 'Y' or answer == 'y'):
            print('bot name: '+sett.get_botname())
            print('Twitch client-id: '+sett.get_clientid())
            print('Twitch token: '+sett.get_token())
            print('Sql username: '+sett.get_sqlusername())
            print('Sql password: '+sett.get_sqlpasswd())
            print('Sql database: '+sett.get_sqldb())
            print('Analysis session time: '+sett.get_session_time())
            print('Favorites: '+str(sett.get_favorites()))
        else:
            sys.exit()
    #analyze
    elif(sys.argv[1] == '-a'):
        try:
            channel_name = sys.argv[2]
            revisions = sys.argv[3]
        except:
            print('error2')
            sys.exit()
            
        from text_analyzing import TextAnalyzing
        from graph import Graph
        
        channel_id = ''
        with open(path / 'Files/channels_dict.txt','r') as f:
            d = f.read().split('\n')
            for line in d:
                if channel_name in line.split(':'):
                    channel_id = line.split(':')[0]
                    break
        if(channel_id != ''):
            TextAnalyzing(channel_id,channel_name,revisions,s)
            print('summary completed successfully')
            g = Graph(channel_id,channel_name,revisions,s)
            g.graph1()
            print('Messages x Time graph created successfully')
            g.graph2()
            print('Users interaction graph created successfully')
            g.graph3()
            print('Users table has created successfully')
            g.graph4()
            print('PCA graphs created (sentiment PCA, messages PCA) successfully')
        else:
            print('no such channel')
    elif(sys.argv[1][0] == '-'):
        print('Unrecognized command, please use -h for help.')
        sys.exit()
    else:
        channel = sys.argv[1]
        try:
            subject = sys.argv[2]
        except:
            subject = ''
        start = True
    
    if(start):
        import pull_emojis
        from bot import TwitchBot
        
        os.system(cm)                
        pull_emojis.get_emojis()
        d = pull_emojis.load_dict()
        bot = TwitchBot(sett.get_botname(), sett.get_clientid(), sett.get_token(), channel, d, s, sett.get_session_time())
        if(get_context(re.sub("[][]",'',subject), bot.get_channel_name()) == 0):
            get_context('boring','')
          
        bot.start() 

#download a context file from wikipedia's API for performing later text summary using NLP    
def get_context(subject,channel):
    import requests
    import urllib.request
    from bs4 import BeautifulSoup
        
    if(subject == ''):
        return 0
    
    url = 'https://en.wikipedia.org/w/api.php?action=opensearch&search='+subject+'&limit=1&namespace=0&format=json'
    try:
        r = requests.get(url, headers=None).json()
    except:
        print("Can't connect to wikipedia's API to download a context file. Continuing with default context file")
        return 0
    if(r[3] != []):
        soup = BeautifulSoup(urllib.request.urlopen(r[3][0]).read(), features="lxml")
        main_tag = soup.findAll('div',{'id':'mw-content-text'})[0]
        text = main_tag.find_all('p')
        context = []
        for line in text:
            s = str(BeautifulSoup(str(line),"lxml").text)
            s = re.sub("[^a-zA-Z-0-9 .,?!)(:;']", '', s)
            context.append(s)
        if(channel != ''):
            if(not os.path.exists(path / 'Channels' / channel)):
                os.mkdir(path / 'Channels' / channel)
            with open(path / 'Channels' / channel / 'context.txt','w+') as f:
                f.write(''.join(context))
            print('Context file downloaded successfully.')
            return 1
        elif(not os.path.exists(path / 'Channels' / channel / 'context.txt')):
            with open(path / 'Channels' / channel / 'context.txt','w+') as f:
                f.write(''.join(context))
            print('Context file downloaded successfully.')
            return 1
    return 0

if __name__ == "__main__":
    main()