# -*- coding: utf-8 -*-
import codecs, pymongo, json, random, time, sys, os
from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING
from sentence_example import sentence_context, sentence_collection
from logger import Logger

class db_client:
    cl = None
    db = None
    word_schema = {}    # main fields of wordforms

    def __init__(self, projectName):
        self.cl = pymongo.MongoClient()
        self.projectName = projectName
        self.init_word_schema(os.path.join(projectName, u'conf/word_schema.json'))
        self.dictGr = {} # category -> list of values
        self.maxTmpArraySize = 104857600 # 100 Mb
        self.logger = Logger()


    def init_word_schema(self, fname):
        f = codecs.open(fname, 'r', 'utf-8')
        self.word_schema = json.loads(f.read())

    
    def create_db(self, dbName):
        self.cl.drop_database(dbName)
        self.db = self.cl[dbName]


    def set_db(self, dbName):
        self.db = self.cl[dbName]


    def leave_essential(self, field, value):
        # recursively leave only those parts of the value
        # which are in the schema, for others, return None
        value_copy = None
        if type(value) == list:
            value_copy = []
            for item in value:
                item_copy = self.leave_essential(field, item)
                if item_copy != None:
                    value_copy.append(item_copy)
            if len(value_copy) <= 0:
                value_copy = None
        
        elif type(value) == dict:
            value_copy = {}
            for subfield in value:
                subvalue_copy = self.leave_essential(field + u'.' + subfield,\
                                                     value[subfield])
                if subvalue_copy != None:
                    value_copy[subfield] = subvalue_copy
            if len(value_copy) <= 0:
                value_copy = None

        else:
            dictTmp = self.word_schema
            # e. g. if the field variable equals "ana.gr.pos",
            # look at word_schema[u'ana'][u'gr'][u'pos']
            for k in field.split(u'.'):
                try:
                    dictTmp = dictTmp[k]
                except KeyError:
                    self.logger.add_message(u'KeyError: ' + field +u', ' + k)
                    return None
            value_copy = value
        return value_copy


    def word_schematize(self, word):
        # leave only those fields which are in the schema
        # (in any case, returns a copy of the input)
        word_copy = {}
        for field in word:
            value = self.leave_essential(field, word[field])
            if value != None:
                word_copy[field] = value
        return word_copy


    def add_word_to_list(self, word, possible_words_list, sentence_id):
        wordStr = json.dumps(word, ensure_ascii=False,\
                             sort_keys=True)
        for possibleWord in possible_words_list:
            possibleWordStr = json.dumps(possibleWord[0],\
                                         ensure_ascii=False,\
                                         sort_keys=True)
            if wordStr == possibleWordStr:
                if len(possibleWord[1]) <= 0 or\
                   possibleWord[1][-1] != sentence_id:
                    possibleWord[1].append(sentence_id)
                possibleWord[2] += 1
                return 0
        possible_words_list.append([word, [sentence_id], 1])
        return 1


    def collect_gr(self, word):
        try:
            for ana in word[u'ana']:
                try:
                    for k, v in ana[u'gr'].iteritems():
                        try:
                            self.dictGr[k].add(v)
                        except KeyError:
                            self.dictGr[k] = set([v])
                except KeyError:
                    pass
        except:
            return

    
    def collect_words(self, sentence, dictWords):
        wordsAdded = 0
        for word in sentence[u'words']:
            word = self.word_schematize(word)
            self.collect_gr(word)
            wf = word[u'wf']
            if len(wf) <= 0:
                continue
            try:
                possible_words_list = dictWords[wf]
                wordsAdded += self.add_word_to_list(word,\
                                                    possible_words_list,\
                                                    sentence[u'_id'])
            except KeyError:
                dictWords[wf] = [[word, [sentence[u'_id']], 1]]
        return wordsAdded

    
    def write_sentences(self, sentences):
        sentLen = len(sentences)
        coll_sentences = self.db.sentences
        dictWords = {} # wf -> list of [word, list of sentence_ids, freq]s
        iSentence = 0
        objIDs = [ObjectId(str(i).zfill(12)) for i in range(1, sentLen + 1)]

        self.logger.add_message(u'\nStarting writing sentences...')
        iPercentDone = 0
        for sentence in sentences:
            sentence[u'_id'] = objIDs[iSentence]
            self.collect_words(sentence, dictWords)
            if iSentence > 0 and (u'first_in_tier' not in sentences[iSentence] or
                                  not sentences[iSentence][u'first_in_tier']):
                sentence[u'prev_id'] = objIDs[iSentence - 1]
            if iSentence < sentLen - 1:
                sentence[u'next_id'] = objIDs[iSentence + 1]
            coll_sentences.insert(sentence)
            iSentence += 1
            if iSentence % 100 == 0:
                iPercentNew = (iSentence * 100) / sentLen
                if iPercentDone / 10 != iPercentNew / 10:
                    self.logger.add_message(str(iPercentNew) + u'% done.')
                iPercentDone = iPercentNew
        self.write_words(dictWords)
        self.logger.add_message(u'Writing sentences: done.')


    def write_words(self, dictWords):
        self.logger.add_message(str(len(dictWords)) +\
                                u' words collected.\r\n\r\n' +\
                                u'Starting writing words...')
        coll_words = self.db.words
        #fOut = codecs.open(u'words_list.json', 'w', 'utf-8')
        for wf in sorted(dictWords):
            for word in dictWords[wf]:
                word[0][u'freq'] = word[2]
                word[0][u'sentence_id'] = word[1]
                coll_words.insert(word[0])
        self.create_indices()
##                fOut.write(json.dumps(word[0], ensure_ascii=False,\
##                           sort_keys=True, indent=2, separators=(',', ': ')))
        #fOut.close()


    def increment_indices(self, categsPerComb, numCategs):
        # (1, 1, 1) -> (1, 1, 2) -> (1, 2, 1) -> ...
        if categsPerComb <= 0 or categsPerComb > numCategs:
            return
        indices = range(categsPerComb)
        while True:
##            if all(indices[i] == numCategs - categsPerComb + i
##                   for i in range(categsPerComb)):
##                return
            for iPlace in range(categsPerComb)[::-1]:
                if indices[iPlace] < numCategs - 1 - (categsPerComb - (iPlace + 1)):
                    indices[iPlace] += 1
                    yield indices
                    break
                else:
                    if iPlace > 0:
                        indices[iPlace] = min([indices[iPlace - 1] + 2,
                                               numCategs - 1 - (categsPerComb - (iPlace + 1))])
                    else:
                        return


    def create_gr_comb_index(self, categsPerComb):
        if categsPerComb <= 0 or categsPerComb > len(self.dictGr):
            return
        coll_words = self.db.words
        categNames = sorted(self.dictGr.keys())
        for indices in self.increment_indices(categsPerComb, len(categNames)):
            indexFields = [(u'ana.gr.' + categNames[i], ASCENDING)
                           for i in indices]
            coll_words.create_index(indexFields)
        

    def create_indices(self):
        self.logger.add_message(u'Starting creating indices...')
        coll_words = self.db.words
        coll_words.create_index(u'wf')
        coll_words.create_index(u'ana.lex')
        coll_words.create_index([(u'wf', ASCENDING), (u'ana.lex', ASCENDING)])
        self.create_gr_comb_index(1)
        self.create_gr_comb_index(2)
        #coll_words.create_index(u'ana.gr.case')


    def find_all(self, collectionName, args, viewArgs={u'_id': 0}):
        coll = self.db[collectionName]
        results = coll.find(args, viewArgs)
        return results


    def find_one(self, collectionName, args, viewArgs={u'_id': 0}):
        coll = self.db[collectionName]
        result = coll.find_one(args, viewArgs)
        return result


    def find_by_word(self, wordTemplate, hint={}):
        # returns all examples of a given word
        words = self.find_all(u'words', wordTemplate)
        if hint != None and len(hint) > 0:
            words.hint(hint)
        try:
            self.logger.add_message(unicode(words.count(True)) +\
                                    u' distinct words found.')
            self.logger.add_message(unicode(words.explain()['nscanned']) +\
                                    u' entries scanned.')
        except:
            pass
        sentenceIDs = set()
        sentenceIDsTmp = []
        numTotal = 0
        numWords = 0
        dictWords = {}  # wordform -> list of words
        for word in words:
            try:
                wf = word[u'wf']
            except KeyError:
                continue
            try:
                dictWords[wf].append(word)
            except KeyError:
                dictWords[wf] = [word]
            numTotal += word[u'freq']
            numWords += 1
            sentenceIDsTmp += word[u'sentence_id']
            # if the temporary array has grown too large,
            # flush its data to the set:
            if sys.getsizeof(sentenceIDsTmp) > self.maxTmpArraySize:
                self.logger.add_message(u'Array size: ' +\
                                        str(sys.getsizeof(sentenceIDsTmp)))
                sentenceIDs |= set(sentenceIDsTmp)
                sentenceIDsTmp = []
        self.logger.add_message(u'Array size: ' +\
                                str(sys.getsizeof(sentenceIDsTmp)))
        sentenceIDs |= set(sentenceIDsTmp)
        sentenceIDsTmp = []
        
##        sentences = self.find_all(u'sentences',\
##                                  {u'_id': {u'$in': list(sentenceIDs)}})
##        numSentences = sentences.count()
        numSentences = len(sentenceIDs)
        self.logger.add_message(str(numWords) + u' distinct words found.')
        self.logger.add_message(str(numTotal) + u' occurrences in ' +\
                                str(len(sentenceIDs)) + u' sentences.')
        self.logger.flush()
        return sentenceIDs, dictWords


def load_sentences(fname, projectName):
    f = codecs.open(os.path.join(projectName, u'data', fname), 'r', 'utf-8')
    sentences = json.loads(f.read())
    print str(len(sentences)) + u' sentences loaded.'
    db = db_client(projectName)
    db.create_db(projectName)
    db.write_sentences(sentences)
    f.close()


##    results = db.find_all(collectionName, args)
##    for res in results[:20]:
##        print u'********\n' * 3
##        print json.dumps(res, ensure_ascii=False,\
##                         indent=2, separators=(',', ': '))
##    print str(results.count()) + u' results found.'

#load_sentences(u'sentences.json', u'greek')
#search_in_db({u'words.ana.lex': u'επί'})
##t1 = time.clock()
##coll = search_in_db({u'ana.gr.case': u'gen', u'ana.gr.number': u'sg'})
####coll = search_in_db({u'ana.gr': {u'case': u'gen', u'number': u'sg'}})
##t2 = time.clock()
##print str(t2 - t1) + u' seconds.'
##text = u''
##for context in coll.contexts(50):
##    text += context.to_text() + u'\n'
##print text
##print u'\nDone.'
if __name__ == u'__main__':
    load_sentences(u'sentences.json', u'yiddish')
