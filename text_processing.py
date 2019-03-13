import os
from pathlib import Path
from bs4 import BeautifulSoup
from textblob import Word
import re
import warnings
    

warnings.filterwarnings("ignore", category=UserWarning, module='bs4')


class TextProcessing():

    path = Path(os.getcwd())
    startpos = -1
    consecutive = False
    words_array = []
    letters_array = []
    
    #Proccess a message for sentiment analysis on the flight from receiving pipe
    def process_message(self, message, nick, d):
        if(self.handle_bots(nick)):
            return False
        message = message.casefold()
        #remove URLs
        message = re.sub(r'http\S+', '', message)
        #clean message from extra backspaces, html/xml tags
        message = BeautifulSoup(message,"lxml").text
        #remove non utf-8 characters in a text
        message = message.encode('utf-8')
        message = message.decode('ascii', 'ignore')
        #handle words where each letter is separated by a space
        #
        self.words_array = []
        self.letters_array = []
        self.connect_words(message)
        message = ''.join(self.words_array)
        #
        #loop goes through every word in a message and compares it 
        #to a known emoji and slang. Then it will replace these cases with acceptable ones for further processing
        hasEmoji = False
        for word in message.split():
            #ignore user names
            if(word[:1] == ''):
                continue
            result = self.handle_slang(word)
            message = message.replace(word,result)
            result = self.handle_emojis(word,d) 
            #word is an emoji
            if(not hasEmoji and result != word):
                hasEmoji = True
                #Handle multiple emojis in one message
                if(result[-1] == '.'):
                    result = result.split('.')[0]
                message = message.replace(word,result,1)
            #word is an emoji, but there is already an emoji present. Remove 1.
            if(hasEmoji and result != word):
                message = message.replace(word,'',1)
                #remove duplicate charachters while keeping word sense
        message = self.delete_duplicates(message)
        #delete excess spaces that could occur due to handleEmoji function (double spaces, spaces at the start and the end of the string)
        message = re.sub(r' +',' ',message).strip()  
        #change all characters to lower case
        if not self.is_not_empty(message):
            return False
        return message
    
                
    #checks if the token in the approved emoji list and if yes, translates it and give it as output
    #if token was not check if it an not approved emoji and if yes return ' ' else return token
    #
    #Example1: 'That was really amazing :D' => token=':D' => ':)' ('That was really amazing :)')
    #Example2: 'That was really amazing TooSpicy' => token='TooSpicy' (approved) => :)' ('That was really amazing :)')
    #Example3: 'That was really amazing ThankEgg' => token='ThankEgg' (not approved) => ' ' (That was really amazing ')
    def handle_emojis(self, token, d):
        #Global emojis and emotes
        #cases to be translated
        with open(self.path / 'Files/dontignore.txt','r') as f:
            for line in f:
                emoji = line.split(',')
                if(token == emoji[0].casefold()):
                    return emoji[1].casefold().replace('\n','').replace('\t','')+'.'
        if token in d:
            return d[token]
        return token
    
    #checks if there's a slang word and replaces it with it's full meaning
    def handle_slang(self, token):
        #cases to be translated
        with open(self.path / 'Files/slang.txt','r') as f:
            for line in f:
                slang = line.split(',')
                if(token == slang[0].casefold()):
                    return slang[1].casefold().replace('\n','').replace('\t','')
        return token
    
    #checks if any message was sent by a known bot
    def handle_bots(self, nick):
        with open(self.path / 'Files/bots.txt','r') as f:
            for line in f:
                line = line.casefold().replace('\n','').replace('\t','')
                if(nick == line):
                    return True
        return False
    
    #if w is a word (separated by 2 spaces, 1 from each side) in s return True else False
    def contains_word(self, s,w):
        return f' {w} ' in f' {s} '
    
    #some words in the chat are sent with spaces in between each letter
    #the function reconstruct them to words, auto-correct them for spelling, and if they make sense ataches
    #them to the text, if not drops the word
    def connect_words(self,message):
        for word in message.split():
            if(len(word) == 1):
                self.letters_array.append(word)
            elif(self.letters_array):
                mystr = ''.join(self.letters_array)
                choose = [i for i in Word(mystr).spellcheck()][0]
                if(choose[1] > 0.5):
                    self.words_array.append(choose[0])
                    self.words_array.append(' ')
                self.letters_array = []
            if(len(word) > 1):
                self.words_array.append(word)
                self.words_array.append(' ')
        if(self.letters_array):
            mystr = ''.join(self.letters_array)
            choose = [i for i in Word(mystr).spellcheck()][0]
            self.words_array.append(choose[0])
        
    #checks if a string is empty or not
    #some strings contain 'invisible' characters that effectively decide that the string is not empty!  
    def is_not_empty(self, s):
        return bool(s and s.strip())
    
    def delete_duplicates(self,message):
        new_message_dict = {}
        m = {}
        i=0
        #real word
        for w in message.split(' '):
            if(w == ''):
                i+=1
                continue
            if(re.sub("[^A-Za-z]",'',w) == ''):
                m[i] = w
                new_message_dict[i] = ''
                i+=1
                continue
            if(Word(w).spellcheck()[0][1] == 1.0):
                new_message_dict[i] = w
                i+=1
                continue
            splitted = self.split_non_alpha(w)
            if(splitted[0] != ''):
                if(Word(splitted[0]).spellcheck()[0][1] == 1.0):
                    new_message_dict[i] = splitted[0]
                else:
                    m[i] = splitted[0]
                    new_message_dict[i] = ''
                i+=1
            if(splitted[1] != ''):
                if(Word(splitted[1]).spellcheck()[0][1] == 1.0):
                    new_message_dict[i] = splitted[1]
                else:
                    m[i] = splitted[1]
                    new_message_dict[i] = ''
                i+=1
        #no items to be further corrected
        if(' '.join([v for k,v in m.items()]) == ''):
            return ' '.join([str(v) for k,v in new_message_dict.items()]) 
        for k,w in m.items():
            l=[]
            t = w
            w+=' '
            while(len(w)>1):
                l.append(tuple((w[0],w[1])))
                w=w[1:]
            f = []
            for e in l:
                if(e[0] != e[1]):
                    f.append(e[0])
            new_word = ''.join(f)
            #emoji
            if(re.sub("[^A-Za-z]",'',new_word) == ''):
                new_message_dict[k] = new_word
                continue
            if(len(new_word) > 4):
                w = Word(''.join(f)).spellcheck()
                if(w[0][1] == 1.0):
                    new_message_dict[k] = ''.join(f)
                else:
                    new_message_dict[k] = t
            else:
                new_message_dict[k] = new_word
        return ' '.join([str(v) for k,v in new_message_dict.items()])
    
    def split_non_alpha(self, s):
        pos = 1
        afirst = True
        if(not s[0].isalpha()):
            afirst = False
        while pos < len(s) and s[pos].isalpha():
            pos+=1
        if(afirst):
            return (s[:pos],s[pos:])
        if(not s[:pos+1].isalpha() and not s[pos+1:].isalpha()):
            return (s[:pos+1],'')
        return (s[:pos+1], s[pos+1:])