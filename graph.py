import plotly as py
import plotly.graph_objs as go
import networkx as nx
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
from shutil import copy2
import re
from textblob import TextBlob
from sklearn.decomposition import PCA as sklearnPCA
from sklearn.preprocessing import StandardScaler
import numpy as np

class Graph:
    
    def __init__(self,channel_id,channel_name,revisions,s):
        self.s = s
        nums = revisions.split('-')
        if(len(nums) == 2):
            self.files_list = range(int(nums[0]),int(nums[1])+1)
        else:
            self.files_list = nums
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.path = Path(os.getcwd()) / 'Channels' / self.channel_name
        #create folder to save the files to if not existant
        if(not os.path.exists(self.path / 'Graphs')):
            os.mkdir(self.path / 'Graphs')    
    
    #Graph1: Messages X Time
    def graph1(self):
        for revision in self.files_list:
            df = pd.read_csv(self.path / 'Data' / str(self.channel_name+'_'+str(revision)+'.csv'))
            total_time = datetime.strptime(df.iloc[-1]['Timestamp'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(df.iloc[0]['Timestamp'], '%Y-%m-%d %H:%M:%S')
            #total session time in minutes
            total_time = abs(total_time.days * 86400 + total_time.seconds)/60
            #markers(one per minute)
            l_x = [x for x in range(0,int(total_time)+1)]
            #first timestamp a message was sent
            minute = datetime.strptime(df.iloc[0]['Timestamp'], '%Y-%m-%d %H:%M:%S')
            #initialize list at minute 0
            l_y = [0]
            #previous message count
            t = 0
            #the amount of messages left if session ended before a minute has passed to count this messages
            x=0
            #time difference between the one minute frame and if any message arrived only after 60 seconds has passed 
            diff = 0
            sum = 0
            possum = 0
            negsum = 0
            #total sentiment
            s_y = [0]
            #positive sentiment
            ps_y = [0]
            #negative sentiment
            ns_y = [0]
            #append to l_y list the amount of messages sent at a time frame
            for index,row in df.iterrows():
                delta = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S') - minute
                senti = TextBlob(row['Message']).sentiment.polarity
                sum += senti
                if(senti >=0):
                    possum += senti
                else:
                    negsum += senti
                if(delta.days * 86400 + delta.seconds + diff >= 60):
                    #basically diff turns to 0
                    if(diff > 0 and delta.days * 86400 + delta.seconds >= 60 - diff):
                        diff += delta.days * 86400 + delta.seconds - 60
                    #calculate diff from time that has passed which is bigger than 60
                    else:
                        diff = delta.days * 86400 + delta.seconds - 60
                    l_y.append(index+1-t)
                    s_y.append(sum)
                    ps_y.append(possum)
                    ns_y.append(negsum)
                    minute = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                    t = index+1
                    sum=possum=negsum=0
                x=index+1
            if(x>0):
                l_y.append(x-t) 
                 
            #draw messages line
            trace1 = go.Scatter(
                x = l_x,
                y = l_y,
                mode = 'lines+markers',
                name = 'Messages'
                )
            
            #draw cumulative sentiment line
            trace2 = go.Scatter(
                x=l_x,
                y=s_y,
                line = dict(
                    width = 4,
                    dash = 'dash'),
                name = 'Cumulative sentiment'
                )
            
            #draw negative sentiment line
            trace3 = go.Scatter(
                x = l_x,
                y = ns_y,
                line = dict(
                    width = 4,
                    color = 'red',
                    dash = 'dash'),
                name = 'Negative sentiment'
                )
            
            #draw positive sentiment line
            trace4 = go.Scatter(
                x = l_x,
                y = ps_y,
                line = dict(
                    width = 4,
                    color = 'green',
                    dash = 'dash'),
                name = 'Positive sentiment'
                )
            
            data = [trace1,trace2, trace3, trace4]
            layout = dict(title = 'Messages, Sentiment x Time distribution',
                          xaxis = dict(title = 'Time'),
                          yaxis = dict(title = 'Messages'))
            fig = dict(data=data, layout=layout)
            py.offline.plot(fig,filename='line_'+str(revision)+'.html',auto_open=False)
            copy2(self.path.parents[1] / str('line_'+str(revision)+'.html'),self.path / 'Graphs')
            os.remove(self.path.parents[1] / str('line_'+str(revision)+'.html'))
    
    #users interaction graph.
    #Each node is a user and each edge represents the connection between users.
    def graph2(self):
        for revision in self.files_list:
            table_name = 'c'+self.channel_id+'_users_'+str(revision)
            G=nx.Graph()
            my_edges = []
            my_nodes =[]
            labels = []
            table = self.s.select(table_name, '*', 'WHERE 1')
            tmp = self.s.select(table_name, 'username', 'WHERE 1')
            #turn sql to list
            user_list = re.sub("[^A-Za-z0-9_ ]",'',str(tmp)).split(' ')
            user_list.append(self.channel_name)
            i = 0
            for row in table:
                if(row[7] != '[]'):
                    for user in re.sub("[^A-Za-z0-9_ ]",'',row[7]).split(' '):
                        try:
                            my_edges.append(tuple((i, user_list.index(user))))
                        except:
                            continue
                        if i not in my_nodes:
                            my_nodes.append(i)
                            labels.append(re.sub("[^A-Za-z0-9_ ]",'',row[0]))
                        if user_list.index(user) not in my_nodes:
                            my_nodes.append(user_list.index(user))
                            labels.append(re.sub("[^A-Za-z0-9_ ]",'',user))
                i += 1
            G.add_nodes_from(my_nodes)
            G.add_edges_from(my_edges)
            
            pos = nx.kamada_kawai_layout(G)
            Xn = [pos[k][0] for k in pos]
            Yn = [pos[k][1] for k in pos]
            
            trace_nodes = dict(type='scatter',
                               x = Xn,
                               y = Yn,
                               mode = 'markers',
                               marker = dict(showscale=True, reversescale=True, colorscale='Viridis',size=[], color=[],
                                                     colorbar=dict(
                                                        thickness=15,
                                                        title='Node messages count',
                                                        xanchor='left',
                                                        titleside='right'
                                                        ),),
                               text = [],
                               hoverinfo = 'text')
            i=0
            table_dict = {}
            while(i<len(table)):
                table_dict.update({table[i][0]:[x for x in table[i][1:]]})
                i+=1
            if self.channel_name not in table_dict:
                table_dict.update({self.channel_name:[0,0,0,0,0.0,[],[]]})
            i=0   
            for node,adjacencies in enumerate(G.adjacency()):
                trace_nodes['marker']['size'].append(len(adjacencies[1])*8)
                trace_nodes['marker']['color'] += tuple([table_dict[labels[node]][0]])
                info = labels[node]+': # of connections: '+str(len(adjacencies[1]))+'\n'+str(table_dict[labels[node]][4])
                trace_nodes['text']+=tuple([info])
                i+=1
                
    
            Xe = []
            Ye = []
            for e in G.edges():
                Xe.extend([pos[e[0]][0], pos[e[1]][0], None])
                Ye.extend([pos[e[0]][1], pos[e[1]][1], None])
            
            trace_edges = dict(type = 'scatter',
                               mode = 'lines',
                               x = Xe,
                               y = Ye,
                               hoverinfo = 'none',
                               line = dict(width = 0.5, color ='#888'))
            
            
            
            axis = dict(showline = False,
                        zeroline = False,
                        showgrid = False,
                        showticklabels = False,
                        title = '')
            
            layout = dict(title = 'Users interaction',
                          autosize = True,
                          showlegend = False,
                          hovermode = 'closest',
                          annotations = [dict(
                              text="**Node size represents its number of connections",
                              showarrow=False,
                              xref="paper", yref="paper",
                              x=0.005, y=-0.002 ) ],
                          xaxis = axis,
                          yaxis = axis)
            
            fig = dict(data=[trace_edges,trace_nodes], layout=layout)
            py.offline.plot(fig,filename='network_'+str(revision)+'.html',auto_open=False)
            copy2(self.path.parents[1] / str('network_'+str(revision)+'.html'),self.path / 'Graphs')
            os.remove(self.path.parents[1] / str('network_'+str(revision)+'.html'))
    
    #export sql table to an html table
    def graph3(self):
        for revision in self.files_list:
            table_name = 'c'+self.channel_id+'_users_'+str(revision)
            table = self.s.select(table_name, '*', 'ORDER BY `npos` DESC')
            i=0
            values=[]
            while(i<len(table[0])):
                lst = [x[i] for x in table]
                values.append(lst)
                i+=1
            trace = go.Table(
                header=dict(values=['User name', '# messages', '# positive messages', '#negative messages', '# neutral messages', 'total sentiment', 'sentiments', 'talking with'],
                            line = dict(color='#7D7F80'),
                            fill = dict(color='#a1c3d1'),
                            align = ['left'] * 5),
                cells=dict(values=values,
                           line = dict(color='#7D7F80'),
                           fill = dict(color='#EDFAFF'),
                           align = ['left'] * 5))
            
            layout = dict(title = 'Users information table', width=1000, height=1000)
            data = [trace]
            fig = dict(data=data, layout=layout)
            py.offline.plot(fig, filename = 'table_'+str(revision)+'.html',auto_open=False)
            copy2(self.path.parents[1] / str('table_'+str(revision)+'.html'),self.path / 'Graphs')
            os.remove(self.path.parents[1] / str('table_'+str(revision)+'.html'))
    
    #PCA
    def graph4(self):
        for revision in self.files_list:
            table_name = 'c'+self.channel_id+'_users_'+str(revision)
            table = self.s.select(table_name, '*', 'WHERE 1')
            total = self.s.select(table_name, 'SUM(nmessages), SUM(npos), SUM(nneg), SUM(nneut)', 'WHERE 1')
            standarized = [[],[],[],[],[],[]]
            real_sent_tags = []
            real_msg_tags = []
            ntalkingto = 0
            for row in table:
                if(re.sub("[^0-9_., ]",'',row[7]).split(',') != ['']):
                    ntalkingto += len(re.sub("[^0-9_., ]",'',row[7]).split(','))
            
            for row in table:
                standarized[0].append(float(row[1])/float(total[0][0]))
                standarized[1].append(float(row[2])/float(total[0][1]))
                standarized[2].append(float(row[3])/float(total[0][2]))
                standarized[3].append(float(row[4])/float(total[0][3]))
                
                nsentiments = len(re.sub("[^0-9_., ]",'',row[6]).split(','))
                sen = float(row[5])/float(nsentiments)
                standarized[4].append(sen)
                
                if(re.sub("[^0-9_., ]",'',row[7]).split(',') == ['']):
                    standarized[5].append(0)
                else:
                    standarized[5].append((len((row[7]).split(','))/float(ntalkingto)))
                
                real_sent_tags.append(self.create_sentiment_tags(sen))
                real_msg_tags.append(self.create_activity_tags(row[1],len((row[7]).split(','))))
            
            real_sent_tags = np.asarray(real_sent_tags)
            real_msg_tags = np.asarray(real_msg_tags)
            X_std = np.asarray(standarized).transpose()
            X_std = StandardScaler().fit_transform(X_std)
            sklearn_pca = sklearnPCA(n_components=2)
            Y_sklearn = sklearn_pca.fit_transform(X_std)
            #sentiment PCA
            names = ['very positive','positive','negative','very negative']
            self.to_smaller_space(real_sent_tags,Y_sklearn,names,revision,'sentiment')
            #messages PCA
            names = ['very active','active','not active','very not active']
            self.to_smaller_space(real_msg_tags,Y_sklearn,names,revision,'messages')

    def to_smaller_space(self,tags,Y,names,revision,fname):
        colors = {'0': '#00ff00', #very active/very positive (green)
                  '1': '#ffff00', #fairly active/fairly positive (yellow)
                  '2': '#ff9800', #not so active/kind of negative (orange)
                  '3': '#ff0000'} #not active/negative (red)
        data = []
        trace = dict()
        for tag,col,name in zip((0,1,2,3),colors.values(),names):
            trace = dict(
                type='scatter',
                x=Y[tags == tag ,0],
                y=Y[tags == tag ,1],
                mode='markers',
                name=name,
                marker=dict(
                    color=col,
                    size=12,
                    line=dict(
                        color='black',
                        width=0.5),
                        opacity=0.8)
            )
            data.append(trace)
        layout = dict(
                hovermode = 'closest',
                xaxis=dict(title='PC1', showline=False),
                yaxis=dict(title='PC2', showline=False)
        )
        fig = dict(data=data, layout=layout)
        py.offline.plot(fig, filename='pca_'+fname+'_'+str(revision)+'.html',auto_open=False)
        copy2(self.path.parents[1] / str('pca_'+fname+'_'+str(revision)+'.html'),self.path / 'Graphs')
        os.remove(self.path.parents[1] / str('pca_'+fname+'_'+str(revision)+'.html'))

    def create_sentiment_tags(self, sen):
        if(sen > 0.5 and sen <= 1):
            tag = 0
        elif(sen >= 0 and sen <= 0.5):
            tag = 1
        elif(sen < 0 and sen >= -0.5):
            tag = 2
        else:
            tag = 3
        return tag
    
    def create_activity_tags(self, nmsg, ntalk):
        if(nmsg >= 30 and ntalk >= 7):
            tag = 0
        elif(nmsg < 30 and nmsg >= 15 and ntalk >= 5):
            tag = 1
        elif(nmsg < 15 and nmsg > 5 and ntalk >= 3):
            tag = 2
        else:
            tag = 3
        return tag

#from settings import Settings
#from sql import Sql
#sett = Settings()
#s = Sql(sett.get_sqldb(), sett.get_sqlusername(), sett.get_sqlpasswd())
#g = Graph('149747285','twitchpresents','1',s)
#g.graph4()
