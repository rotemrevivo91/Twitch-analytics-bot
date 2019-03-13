# TUHH (Technische Universität Hamburg) Computer Science (Bachelor) Internship W18/19

## Twitch analytical bot

A 6-weeks software development internship in the field of natural language processing.
In these 6 weeks i will learn the workflow of software development and get my first experience in the field.

**Place of internship:** *ZMNH (Zentrum für Molekulare Neurobiologie Hamburg)*

---

## Goal, Purpose and usage

The bots `goal` is to perform analytics on a twitch chat stream and return meaningful data to the channel's streamer.


The `purpose` of the project is:
* Learn Python
* Learn how do text processing and text analysis with machine learning techniques.
* Learn how to create a text classifier.
* Try different datasets for sentiment analysis (Different channels have different quality of chat).

**The bot's `usage` and quality of analysis rely a lot on the type of stream and chat present.

---
## Requirements

* Python 3.6
* MySql (For Windows: use xampp for example)

---
## Installation

Pull the project and install the dependencies:
```
pip install -U -r requirements.txt
```
---
## Usage

    >> python SentiBot.py -h
    >>
    ###################################################################################################################################
    #                                                        SentiBot v1.0                                                            #
    #                                                                                                                                 #
    # python sentibot <channel_name> [context] - joins a channel                                                                      #
    # python sentibot -f <channel_number> [context] - chooses a channel from favorites list to join to                                #
    # python sentibot -sf - shows all favorite channels                                                                               #
    # python sentibot -rf <channel_number> - removes a favorite channel from the list                                                 #
    # python sentibot -af - opens a menu to add new favorites channels                                                                #
    # python sentibot -st <time_minutes> - change session time per analysis                                                           #
    # python sentibot -s - opens the settings menu for update                                                                         #
    # python sentibot -ss - show all settings                                                                                         #
    # python sentibot -a <channel_name> <1-n> - analyze data files of a channel                                                       #
    #                                                                                                                                 #
    # *   <> - obligatory field , [] - optional field                                                                                 #
    # **  Exit and save csv file and potential analyze (if data set not too small): ctrl+c                                            #
    # *** optional context will download a file for text analysis. context could be name of a game/show showed in the channel.        #
    #     When not mentioned a default context file will be used for analyzing the data. context should be captioned in [] and could  #
    #     contain multiple words separated by an underscore (Ex: python sentibot examplechannel [dr._who])                            #
    ###################################################################################################################################

---

## Motivation

* *Why did I choose machine learning field?*

The field of machine learning has interested me for some time now. One can say It has all started thanks to Hollywood, when I first watched a show that describes an A.I that is able to track people thanks to security cameras, phone tapping and facial recognition all happening in matter of milliseconds, not only that but the machine could understand human nuances, different languages and analyzing texts. This has fascinated me ever since.
Also, after I’ll finish my Computer Science Bachelor I plan to apply for a Master degree in machine learning, and I would like to use this internship opportunity to brighten my horizons in the field, and get a head start.

* *What is the goal of the project?*

The goal of the project is to have my first experience programming in a new language (Python) and try
many different tools and libraries that will help me gain experience in NLP machine learning for the future.

* *What is NLP?*

“Natural Language Processing (NLP) is a subfield of Artificial Intelligence that is focused on enabling computers to understand and process human languages, to get computers closer to a human-level understanding of language. Computers don’t yet have the same intuitive understanding of natural language that humans do. They can’t really understand what the language is really trying to say. In a nutshell, a computer can’t read between the lines.
That being said, recent advances in Machine Learning (ML) have enabled computers to do quite a lot of useful things with natural language! Deep Learning has enabled us to write programs to perform things like language translation, semantic understanding, and text summarization. All of these things add real-world value, making it easy for you to understand and perform computations on large blocks of text without the manual effort.” ([Source][1])

* *Why did I choose to work with NLP?*

NLP is one of the most researched machine learning fields, it’s a good starting point to understand the workflow of an artificial neural network.

---
## Work environment

* Python
* NLTK
* TextBlob
* Gensim
* SciKit
---
## Project planning

1. _Research:_
    * [introduction to ANN - Understanding the concepts][2]
    * [Machine learning - text processing][3]
    * [Deep Learning for Sentiment Analysis: A Survey][4]
    * Text analysis (Text summary)
2. _Software development:_
    * Text preprocessing ("cleanup"): Every incoming message has to go through a cleaning process.
        * Ignore messages that were sent by bots (compare usernames to known bots list)
        * Ignore incoming commands (messages that start with '!')
        * Ignore messages of length 1.
        * Remove URLs, extra backspaces, non utf-8 characters.
        * Twitch special case: Clean all emotes that has no sentiment and translate twitch emotes to meaningful ones that are interpretable by Textblob.
        How it works: each emote is composed of two words, first word is usually an abbreviation of the caster's username and the second word is the 'meaning'
        of the emote. By sentiment analyzing the second word there's a good chance of understanding the sentiment of the emote.
        Emotes are translated to 4 global emotes that are known to work for TextBlob's sentiment analysis:
        :D (High positive sentiment), :P (Relatively high positive sentiment), :) (Positive sentiment), :( (Negative sentiment).
        There's an available [API](https://twitchemotes.com/api_cache/v3/) for all of Twitch's emotes.
        Apart from Twitch's propriety there's an allowed emotes list, that are translated manually.
        * Each word in a message is compared to a list of known slangs (i.e., abbreviation) and translated to their long version for sentiment analysis and text summary.
        * some words in the chat are sent with spaces in between each letter:
        reconstruct them to words, auto-correct them for spelling (TextBlob), and if they make sense attaches
        them to the text, if not drops the word
        * Delete consecutive duplicate letters while keeping real words with consecutive duplicate letters intact.
        * Save preprocessed messages including username and timestamp as a csv. file.
    * Text analysis:
        * Loading csv. and constructing a single text with sentences separated by points '.'
        * Text summary:
            * Part-of-speech (POS) frequency text summary: Based on "[Foray's into part of speech](http://infomotions.com/blog/2011/02/forays-into-parts-of-speech/)"
            Constructing a 9-space vector (Adjective, Adverb, Conjunction, Determiner, Noun, Numeral, Particle, Pronoun, Verb. From a 32 different POS tags. Similar POS tags are grouped together.) based on the average POS tagging frequency of 9 different corpuses.
            For each sentence in the text to analyze, construct of POS frequency vector and calculate the euclidean distance between the vectors.
            Vectors with closest euclidean distance are chosen for the text summary.
            * Context based text summary: A context file is downloaded from [Wikipedia's API](https://en.wikipedia.org/w/api.php?action=opensearch&search=&limit=1&namespace=0&format=json).
            Context file is broken down to words in-order to create a Bag-of-Words (BoW) to construct an NLP classifier (on an already trained gensim network).
            Same happens with the text incoming from the csv. file. In this method, instead of calculating the euclidean distance of between single words, the cosine distance is calculated.
            Best sentences will be the ones that their individual words' cosine distance is the lowest (smallest angle) and in a sentence view smallest cumulative angle.
            The quality of text summary based of this method is highly dependent if the chat speaking about the subject of the stream (For example a stream about Fortnite with a chat talking about Fortnite related theme) and also the quality of information given from the context file.
            There are cases where no context based summary will not be created because the data given is not good enough.
        * Creating an SQL table with the following information: number of messages sent, number of positive/negative/neutral messages sent, cumulative sentiment of a user, each individual message sentiment, a list of users the subject is talking with.
        SQL database has a very quick response time to queries is therefore optimal for keeping information that will later be exported to graph form.
    * Graphs plotting: Using Plotly library to create meaningful graphical interpretation of a stream's chat (a SVG integrated in an HTML format).
        * Graph 1: Messages, Sentiment over Time. A line chart, represents the amount of messages and cumulative sentiment (every 60 seconds). Very useful in order to see where when "bursts" events occurs and their sentiment (bursts means a big spike in the amount of messages).
        * Graph 2: Users interaction graph. Plotting a network graph where each node is a user and each edge is an interaction between the two connected nodes. Node size represents the number of connection it has with other nodes. Node's color represents the number of messages that were sent by the node.
        * Graph 3: Exporting the SQL table to HTML.
        * Graph 4: PCA (Principal component analysis) - Finding the directions of maximum variance in high-dimensional data and project it onto a smaller dimensional subspace while retaining most of the information. In this case turning a 6 dimensional space to a 2 dimensional space.
    * Offline support: The bot should be able to work in an "offline" mode and perform analysis on given csv. files.
        * Full analysis: Graphs plotting and text summary.
        * Analysis of multiple files at once.
        * Changing the bot's settings
3. _Testing_:
    * Windows and Linux support
    * Extreme chat cases (high amount of messages in short period of time)
    * Input that causes crashes
    * Correct graph plotting
    * Meaningful text summary

---
### Schedule

* Week 1: Research
* Week 2-4: Software development
* Week 5: Testing
* Week 6: Finalizations

---
## Limitations

* In 6-weeks there is no time developing my own ANN.
* Learning the mathematics behind how an ANN would take a lot more time than 6-weeks.
* Developing a 100% working sentiment analysis is impossible with the resources and time at my disposal (mistakes are to be expected).
* Not focusing on design, only functionality.

---
## Known issues

* NumPy error when using Python 3.7+
* When using anaconda environment capturing ctrl+c just quits the program and doesn't captures the signal.
* Can't connect to IRC channels from behind a proxy.

---
## Expanding possibilities

* Adding more graphs
* Improving the text summary option by training an ANN per game (non-stream-dependent)
* Improving the sentiment analysis for emotes and messages by training my own sentiment analyzer.
* Tweets analysis in offline mode: Twitter has some of the same features as Twitch - '@' for tagging a person and emotes.

---
## Tools used for development

* Eclipse
* Jupyter Notebook
* Anaconda

Tested on: Windows 10, Ubuntu 16.04, 18.04 (With and without anaconda environment)

---
## Sources

### NLP
* [introduction to ANN](https://medium.com/@datamonsters/artificial-neural-networks-for-natural-language-processing-part-1-64ca9ebfa3b2)
* [sentiment analysis demo](https://monkeylearn.com/sentiment-analysis/#sentiment-analysis-demo)
* [text processing + sentiment analysis](http://text-processing.com/)
* [introduction to Natural Language Processing](https://towardsdatascience.com/an-easy-introduction-to-natural-language-processing-b1e2801291c1)
* [NLTK+SpaCy guide#1](https://towardsdatascience.com/named-entity-recognition-with-nltk-and-spacy-8c4a7d88e7da)
* [NLTK+SpaCy github](https://github.com/susanli2016/NLP-with-Python/blob/master/NER_NLTK_Spacy.ipynb)
* [word2vec TensorFlow tutorial](https://www.tensorflow.org/tutorials/representation/word2vec)
* [word2vec source](https://code.google.com/archive/p/word2vec/)
* [word2vec examples](https://medium.com/swlh/playing-with-word-vectors-308ab2faa519)
* [word2vec in python using gensim and NLTK](https://streamhacker.com/2014/12/29/word2vec-nltk/)

[1]: https://towardsdatascience.com/an-easy-introduction-to-natural-language-processing-b1e2801291c1
[2]: https://medium.com/@datamonsters/artificial-neural-networks-for-natural-language-processing-part-1-64ca9ebfa3b2
[3]: https://towardsdatascience.com/machine-learning-text-processing-1d5a2d638958
[4]: https://arxiv.org/ftp/arxiv/papers/1801/1801.07883.pdf
[5]: http://ai.stanford.edu/~amaas/papers/wvSent_acl2011.pdf

---
## About me
My name is Rotem Revivo,I'm a 27-years old Computer Science student at the TUHH (Technische Universität Hamburg).
I have background in programming in: C#, C, C++, Java, Javascript, HTML, PHP.


