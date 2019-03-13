import pandas as pd
import os
from pathlib import Path
from textblob import TextBlob
import heapq
import math

import warnings
from docutils.nodes import revision
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
warnings.filterwarnings(action='ignore', category=FutureWarning, module='gensim')
import gensim
from gensim.summarization.summarizer import summarize

class TextAnalyzing():
    
    #http://infomotions.com/blog/2011/02/forays-into-parts-of-speech/
    
    #other and noun are together
    #preposition is together with conjunction
    #symbols and punctuation are not recognized
    def __init__(self,channel_id,channel_name,revisions,s):
        self.s = s
        nums = revisions.split('-')
        if(len(nums) == 2):
            self.files_list = range(int(nums[0]),int(nums[1])+1)
        else:
            self.files_list = nums
        self.channel_name = channel_name
        self.channel_id = channel_id
        self.path = Path(os.getcwd()) / 'Channels' / self.channel_name
        self.text = ''
        # Adjective, Adverb, Conjunction, Determiner, Noun, Numeral, Particle, Pronoun, Verb
        self.pos_dict = {'JJR' : 'JJ', 'JJS' : 'JJ', 'JJ' : 'JJ',
                    'RBR' : 'RB', 'RBS' : 'RB', 'WRB' : 'RB', 'RB' : 'RB',
                    'IN' : 'CC', 'CC' : 'CC',
                    'PDT' : 'DT', 'WDT' : 'DT', 'DT' : 'DT',
                    'NNS' : 'NN', 'NNP' : 'NN', 'NNPS' : 'NN', 'NN' : 'NN',
                    'CD' : 'CD',
                    'RP' : 'RP',
                    'PRP' : 'PN', 'PRP$' : 'PN', 'WP' : 'PN', 'WP$' : 'PN',
                    'VBD' : 'VB', 'VBG' : 'VB', 'VBN' : 'VB', 'VBP' : 'VB', 'VBZ' : 'VB', 'VB' : 'VB'
                    }
        self.pos_ranks = {'JJ' : 6,'RB' : 7, 'CC' : 17, 'DT' : 10, 'NN' : 34, 'CD' : 1, 'RP' : 1, 'PN' : 9, 'VB' : 15}
        
        if(not os.path.exists(self.path / 'Summaries')):
            os.mkdir(self.path / 'Summaries')
        self.read_csv()
    
    #read a csv file and create text summaries in two different methods
    def read_csv(self):
        for revision in self.files_list:
            df = pd.read_csv(self.path / 'Data' / str(self.channel_name+'_'+str(revision)+'.csv'), encoding='utf-8')
            users_dict = {}
            #how many messages each user has sent
            for index,row in df.iterrows():
                if row['Nick'] in users_dict:
                    sentiment = self.check_sentiment(row['Message'])
                    #calculate total sentiment on the fly
                    users_dict[row['Nick']][4] = (users_dict[row['Nick']][4] * users_dict[row['Nick']][0] + sentiment[1]) / (users_dict[row['Nick']][0] + 1)
                    users_dict[row['Nick']][0] += 1
                    users_dict[row['Nick']][sentiment[0]] += 1
                    users_dict[row['Nick']][5].append(sentiment[1])
                    l = self.talking_to(str(row['Message']))
                    for e in l:
                        if e in users_dict[row['Nick']][-1]:
                            l.remove(e)
                    users_dict[row['Nick']][-1] += l
                else:
                    # [0 #messages, 1 #pos, 2 #neg, 3 #neut, 4 total sentiment, 5 sentiments[], 6 talkting_to[]]
                    info = [1,0,0,0,0,[],[]]
                    sentiment = self.check_sentiment(row['Message'])
                    info[sentiment[0]] = 1
                    info[4] = sentiment[1]
                    info[5].append(sentiment[1])
                    info[-1] = self.talking_to(row['Message'])
                    users_dict[row['Nick']] = info
                #build text for summary
                self.text += str(row['Nick']+':'+row['Message']) + ' . '
            self.to_sql('c'+self.channel_id+'_users_'+str(revision), users_dict)
            self.text_summary_pos_freq(revision)
            self.text_summary_context(revision)
            self.gensim_text_summary(revision)
            self.text = ''
    
    #creates a text summary based of POS tags frequency in a given text (per sentence)
    #seems to work better for meaningful longer sentences
    #https://en.wikipedia.org/wiki/Euclidean_distance
    def text_summary_pos_freq(self,revision):
        blob = TextBlob(self.text)
        l = {}
        sentence_list = blob.sentences
        #Break text to sentences
        for sent in sentence_list:
            freq_tupple_lsit = []
            #get POS tags of each sentence
            tags = sent.tags
            #a list of every word in the sentence and its number of occurrences in it
            count = sent.word_counts
            #work with only sentences with 20+ words as they have higher chance being grammatically correct and match the pattern
            if(sum(count.values()) > 15):
                for tag in tags:
                    #build a tuple frequency list constructed from (POS tag : number of occurrences)
                    freq_tupple_lsit.append((tag[1],count[tags[0][0]]))
                    freq_tupple_dict = {}
                    for tup in freq_tupple_lsit:
                        #key already in dictionary
                        if(tup[0] in freq_tupple_dict.keys()):
                            freq_tupple_dict[tup[0]] += 1
                        #first occurrence
                        else:
                            freq_tupple_dict[tup[0]] = 1
                current_ranks = {}
                #calculate the percentage of each POS tag in the sentence: 
                # (number of occurrences / sum of all occurrences of all POS tags)*100 = %
                for key in freq_tupple_dict:
                    current_ranks[key] = int((freq_tupple_dict[key]/sum(count.values()))*100)
                new_dict = {}
                #translate global POS tags using POS dictionary to create a more suitable pattern matching
                for key in current_ranks:
                    if(key in self.pos_dict.keys()):
                        new_dict[self.pos_dict[key]] = current_ranks[key]
                t = {}
                for key in self.pos_ranks:
                    if key not in new_dict:
                        t[key] = 0
                    else:
                        t[key] = new_dict[key]
                #eculidean distance
                l[sent] = self.euclidean_distance([self.pos_ranks[k] for k in self.pos_ranks],[t[k] for k in t])
        a = heapq.nsmallest(4, l, key=l.get)
        summary_sentences = ''
        for x in a:
            summary_sentences += str(x)+'\n'
        with open(self.path / 'Summaries' / str('possum_'+str(revision)+'.txt'),'w+') as f:
            f.write('Part-of-speach (POS) summary:\n\n'+summary_sentences)
    
    def text_summary_context(self,revision):
        context = False
        if(os.path.exists(self.path / 'context.txt')):
            with open(self.path / 'context.txt','r') as f:
                context_data = TextBlob(f.read())
                context = True
        else:
            with open(self.path.parents[0] / 'context.txt','r') as f:
                context_data = TextBlob(f.read())            
        l={}
        #Break text to sentences
        sentence_list = context_data.sentences
        word_frequencies = gensim.corpora.Dictionary(sentence_list)
        corpus = [word_frequencies.doc2bow(s) for s in sentence_list]
        tf_idf = gensim.models.TfidfModel(corpus)
        index = gensim.similarities.SparseMatrixSimilarity(tf_idf[corpus],num_features=len(word_frequencies))
        query_data = TextBlob(self.text).sentences
        #connect sentences that belong to the same message
        query_sentences = []
        acc = ''
        for x in query_data:
            if(x.find(':') != -1):
                if(acc != ''):
                    query_sentences.append(TextBlob(acc))
                    acc = ''
                acc = str(x)
            else:
                acc += str(x)
        query_sentences = [s for s in query_sentences if len(s.words)>15]
        #for s in query_sentences:
        #    print(TextBlob(s.split(':')[1]))
        query_doc = [word_frequencies.doc2bow(TextBlob(s.split(':')[1])) for s in query_sentences]
        sims = index[tf_idf[query_doc]]
        ix = 0
        try:
            for y in sims:
                t = [x for i,x in enumerate(y)]
                if(context):
                    score = 70
                else:
                    score = 50   
                if(max(t)*100 > score):
                    l[query_sentences[ix]] = max(t)*100
                ix += 1
            summary_sentences = ''
            for k,v in l.items():
                summary_sentences += str(k)+'\n'
            with open(self.path / 'Summaries' / str('consum_'+str(revision)+'.txt'),'w+') as f:
                f.write('Context summary:\n\n'+summary_sentences)
        except TypeError:
            return ''
    
    def gensim_text_summary(self,revision):
        with open(self.path / 'Summaries' / str('gensim_'+str(revision)+'.txt'),'w+') as f:
            f.write('Gensim (TextRank algorithm) summary:\n\n'+summarize(self.text, ratio=None, word_count=200, split=None))
    
    #sentiment per message
    def check_sentiment(self,message):
        sentiment = TextBlob(str(message)).sentiment.polarity
        if(sentiment > 0):
            return [1,sentiment]
        elif(sentiment < 0):
            return [2,sentiment]
        return [3,sentiment]
        
    #recognize named entites in messages
    def talking_to(self,message):
        l = []
        for w in message.split(' '):
            if('@' in w):
                if(w[1:] not in l):
                    l.append(w[1:])
        return l
    
    #export data to sql table
    def to_sql(self,name,d):
        values = '(username VARCHAR(255), nmessages int, npos int, nneg int, nneut int, sentiment float, sentiments TEXT, talkingto TEXT)'
        self.s.create_table(name, values)
        values = '(username, nmessages, npos, nneg, nneut, sentiment, sentiments, talkingto)'
        #insert values to table
        for key in d:
            self.s.insert(name, values, (key, int(d[key][0]), int(d[key][1]), int(d[key][2]), int(d[key][3]), float(d[key][4]), str(d[key][5]), str(d[key][6])))
    
    def euclidean_distance(self,p,q):
        return math.sqrt(sum([(p[k]-q[k])**2 for k in range(len(p))]))