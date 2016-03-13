import pymongo, random, time
from words_highlighter import *

class sentence_context:
    def __init__(self, _curSent, _wordHighlighter, _dbClient):
        self.curSent = _curSent
        self.wordHighlighter = _wordHighlighter
        self.dbClient = _dbClient
        self.prevSent = []
        self.nextSent = []
        self.expanded = 0  # number of adjacent sentences already loaded
        

    def load_adjacent(self, qty):
        # load qty adjacent sentences to those already loaded
        if qty > 0:
            self.expanded += qty
        for i in range(qty):
            try:
                if len(self.prevSent) <= 0:
                    prevID = self.curSent[u'prev_id']
                else:
                    prevID = self.prevSent[-1][u'prev_id']
                prevS = self.dbClient.find_one(u'sentences', {u'_id': prevID})
                if prevS != None and prevS[u'doc'] == self.curSent[u'doc']:
                    self.prevSent.append(prevS)
            except KeyError:
                pass

            try:
                if len(self.nextSent) <= 0:
                    nextID = self.curSent[u'next_id']
                else:
                    nextID = self.nextSent[-1][u'next_id']
                nextS = self.dbClient.find_one(u'sentences', {u'_id': nextID})
                if nextS != None and nextS[u'doc'] == self.curSent[u'doc']:
                    self.nextSent.append(nextS)
            except KeyError:
                pass
            
    def to_text(self, context=0):
        self.load_adjacent(context - self.expanded)
        words = []
        for i in range(context)[::-1]:
            try:
                words += self.prevSent[i][u'words']
            except:
                pass
        words += self.curSent[u'words']
        for i in range(context):
            try:
                words += self.nextSent[i][u'words']
            except:
                pass
        text = self.wordHighlighter.words2text(words)
        return text

    def highlight_words(self):
        self.curSent[u'words'] = self.wordHighlighter.highlight_words(self.curSent[u'words'])


class sentence_collection:
    def __init__(self, _ids, _wordsToHighlight, _queryTemplates,\
                 _dbClient, randomize=True):
        #t1 = time.clock()
        self.sentenceIDs = list(_ids)
        if randomize:
            random.shuffle(self.sentenceIDs)
        self.wordHighlighter = WordHighlighter(_wordsToHighlight, _queryTemplates)
        self.dbClient = _dbClient
        #t2 = time.clock()
        #print u'sentence_collection initialization done in ' + str(t2 - t1) + u' s'
        
        self.cursor = None
        self.sentence_count = len(self.sentenceIDs)
        self.examples = {}  # example no. -> example
##        if self.sentence_count > 0:
##            self.examples = [None] * self.sentence_count


    def fill_examples(self, start, n):
        sentencesToLoad = []
        examplesToFill = []
        for iExample in range(start, start + n):
            if iExample not in self.examples or\
               self.examples[iExample] is None:
                examplesToFill.append(iExample)
                sentencesToLoad.append(self.sentenceIDs[iExample])
        if len(sentencesToLoad) <= 0:
            return
        # find all lacking examples
        t1 = time.clock()
        self.cursor = self.dbClient.find_all(u'sentences',\
                                    {u'_id': {u'$in': sentencesToLoad}})
        t2 = time.clock()
        print u'Cursor obtained in ' + str(t2 - t1) + u' s'

        t1 = time.clock()
        iSentence = 0
        for sent in self.cursor:
            self.examples[examplesToFill[iSentence]] =\
                sentence_context(sent,\
                                 self.wordHighlighter,\
                                 self.dbClient)
            iSentence += 1
        t2 = time.clock()
        print u'Sentences obtained in ' + str(t2 - t1) + u' s, ' +\
              str(self.cursor.count()) + u' examples filled.'
        
        
    def contexts(self, n, start=0):
        if n <= 0 or start >= self.sentence_count:
            return
        if start < 0:
            start = 0
        if start + n > self.sentence_count:
            n = self.sentence_count - start
        self.fill_examples(start, n)
        for iExample in range(start, start + n):
            yield self.examples[iExample]
        
        
