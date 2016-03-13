import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import time, random
from db_client import db_client
from words_highlighter import *
from sentence_example import sentence_context, sentence_collection
from pymongo import ASCENDING, DESCENDING
from bson import json_util
import json
import codecs

class QueryParser:
    def __init__(self, projectName):
        self.projectName = projectName
        self.db = db_client(projectName)
        self.highlighter = WordHighlighter()

    def collect_keys(self, template):
        keys = set()
        if type(template) == list:
            for el in template:
                keys |= self.collect_keys(el)
        elif type(template) == dict:
            keys |= set(template.keys())
            for v in template.values():
                keys |= self.collect_keys(v)
        return keys
    
    def make_hint(self, wordTemplate):
        keys = self.collect_keys(wordTemplate)
        hint = {}
        if u'wf' in keys and (u'ana.lex' in keys or\
                              (u'ana' in keys and u'lex' in keys)):
            hint = [(u'wf', ASCENDING), (u'ana.lex', ASCENDING)]
            return hint
        grKeys = [key for key in keys if key.startswith(u'ana.gr.')]
        if len(grKeys) >= 2:
            random.shuffle(grKeys)
            grKeys = grKeys[:2]
            hint = [(key, ASCENDING) for key in sorted(grKeys)]
        elif u'wf' in keys:
            hint = [(u'wf', ASCENDING)]
        elif u'ana.lex' in keys:
            hint = [(u'ana.lex', ASCENDING)]
        elif len(grKeys) == 1:
            hint = [(grKeys[0], ASCENDING)]
        print hint
        return hint

    def positions_comply(self, sID, queryTemplates):
        # check if words in the sentence comply with the query
        cursor = self.db.find_one(u'sentences', {u'_id': sID})
        sentence = cursor[0]
        self.highlighter.wordsToHighlight = [qt[1] for qt in queryTemplates]
        self.highlighter.queryTemplates = [qt[0] for qt in queryTemplates]
        return self.highlighter.highlight_sentence(sentence[u'words'], True)
        
    def intersect_sentences(self, wordSentenceIDs, wordDictionaries,\
                            queryTemplates):
        if len(wordSentenceIDs) <= 0 or\
           any([len(s) <= 0 for s in wordSentenceIDs]):
            return []
        sentenceIDs = wordSentenceIDs[0]
        for iWord in range(1, len(queryTemplates)):
            sentenceIDs &= wordSentenceIDs[iWord]
            if len(sentenceIDs) <= 0:
                return []
        resultIDs = []
        
        queryTemplatesShort = [(queryTemplates[0], wordDictionaries[0])] +\
                               [(queryTemplates[i], wordDictionaries[i])\
                                for i in range(1, len(queryTemplates))\
                                if u'pos' in queryTemplates[i]]
        if len(queryTemplatesShort) <= 1:
            return list(sentenceIDs)
        for sID in sentenceIDs:
            if self.positions_comply(sID, queryTemplatesShort):
                resultIDs.append(sID)
        return resultIDs
    
    def search_one_word(self, wordTemplate):
        self.db.set_db(self.projectName)
        hint = self.make_hint(wordTemplate)
        return self.db.find_by_word(wordTemplate, hint)

    def search(self, queryTemplates):
        # one for each word in the query:
        wordDictionaries = []
        wordSentenceIDs = []
        for wordTemplate in queryTemplates:
            sentenceIDs, dictWords = self.search_one_word(wordTemplate)
            wordDictionaries.append(dictWords)
            wordSentenceIDs.append(sentenceIDs)
        if len(queryTemplates) == 1:
            return sentence_collection(wordSentenceIDs[0],\
                                       wordDictionaries, queryTemplates, self.db)
        sentenceIDs = self.intersect_sentences(wordSentenceIDs,\
                                               wordDictionaries, queryTemplates)
        return sentence_collection(sentenceIDs, wordDictionaries,\
                                   queryTemplates, self.db)


if __name__ == u'__main__':
    t1 = time.clock()
    qp = QueryParser(u'yiddish')    # создать объект нужно один раз
##    coll = qp.search_one_word({u'ana.gr.case': u'gen', u'ana.lex': u'ομάδα'},\
####                               u'greek')
##    coll = qp.search_one_word({u'ana.gr.case': u'gen', u'ana.lex':\
##                               {u'$regex': u'^ο.*άδα'}},\
##                               u'greek')
    coll = qp.search([{u'ana.gr.case': u'nom/acc/dat', u'ana.lex':\
                      {u'$regex': u'^z.*'}}])  # запрос: в простом случае это массив
    # С одним словарём, в котором ключи соответствуют непустым поисковым полям;
    # подробнее нужно смотреть в справку mongodb о том, как выглядят запросы к БД.
    
    t2 = time.clock()
    print str(t2 - t1) + u' seconds.'

    results = []
    for context in coll.contexts(20):  # эта функция выдаёт объекты sentence_context
        # в запрошенном количестве (или меньше, если не нашлось)
        #text += context.to_text() + u'\n'
        context.load_adjacent(2)    # К каждому контексту подгрузить по два соседних предложения
        context.highlight_words()   # Подсветить в контекстах искомые слова (добавить к ним highlight=True)
        results.append(context.prevSent + [context.curSent] + context.nextSent)
        # добавить к результатам массив из двух предложений слева, искомого предложения
        # и двух предложений справа
    text = json.dumps(results, ensure_ascii=False, indent=2,
                      default=json_util.default) # а вот так из этого делается json
    # То, что ниже, тебе уже не нужно.
    fOut = codecs.open(u'test_out/sentence_out_example_yiddish1.json', 'w', 'utf-8-sig')
    fOut.write(text)
    fOut.close()
    print u'\nDone.'
