import re

class WordHighlighter:
    def __init__(self, _wordsToHighlight=None, _queryTemplates=None):
        if _wordsToHighlight is None:
            _wordsToHighlight = []
        if _queryTemplates is None:
            _queryTemplates = []
        self.wordsToHighlight = _wordsToHighlight
        self.queryTemplates = _queryTemplates
        #self.build_regex()

    def build_regex(self):
        # builds a regex which handles all wordforms
        regexText = u'^(?:'
        regexText += u'|'.join(self.wordsToHighlight.keys())
        regexText += u')$'
        self.regexWf = re.compile(regexText, flags=re.I|re.U)
        
    def obj_coincides(self, objToCheck, objReference):
        # recursively check if all key-value pairs in objReference,
        # except "freq" and "..._id", are also contained in dictToCheck
        if type(objToCheck) != type(objReference):
            return False
        if type(objToCheck) == dict:
            for k, v in objReference.iteritems():
                if k == u'freq' or k.endswith(u'_id'):
                    continue
                try:
                    vToCheck = objToCheck[k]
                    if self.obj_coincides(vToCheck, v) == False:
                        return False
                except KeyError:
                    return False
        elif type(objToCheck) == list:
            # find a correspondence for each element of objToCheck
            if len(objToCheck) != len(objReference):
                return false
            for item in objReference:
                bCorrespondenceFound = False
                for itemToCheck in objToCheck:
                    if self.obj_coincides(itemToCheck, item) == True:
                        bCorrespondenceFound = True
                        break
                if bCorrespondenceFound == False:
                    return False
        else:
            if objReference != objToCheck:
                return False
        return True

    def make_sentence_scheme(self, words):
        wordScheme = [] # each element is a list of query part numbers
                        # it complies with
        mainWordPositions = []  # positions of the words for the first query
        for iWord in range(len(words)):
            wordScheme.append([])
            for iQueryPart in range(len(self.queryTemplates)):
                if self.check_word(words[iWord], iQueryPart):
                    wordScheme[-1].append(iQueryPart)
                    if iQueryPart == 0:
                        mainWordPositions.append(iWord)
        return wordScheme, mainWordPositions

    def highlight_sentence(self, words, checkForExistence=False):
        wordScheme, mainWordPositions = self.make_sentence_scheme(words)
        for iQueryPart in range(len(self.queryTemplates)):
            try:
                posRange = self.queryTemplates[iQueryPart][u'pos']
            except KeyError:
                continue
            numWords = 0
            for mainWordPos in mainWordPositions[:]:
                rangeL = mainWordPos - posRange[0]
                if rangeL < 0:
                    rangeL = 0
                rangeR = mainWordPos + posRange[1]
                if rangeR > len(sentence[u'words']):
                    rangeR = len(sentence[u'words'])
                wordFoundInRange = False
                for iWord in range(rangeL, rangeR):
                    if iQueryPart in wordScheme[iWord]:
                        wordFoundInRange = True
                        if not checkForExistence:
                            words[iWord][u'highlighted'] = True
                if wordFoundInRange:
                    numWords += 1
                else:
                    mainWordPositions.remove(mainWordPos)
            if numWords <= 0:
                if checkForExistence:
                    return False
                return words
        if checkForExistence:
            return True
        return words
    
    def check_word(self, word, iQueryPart=0):
        # returns True iff the word should be highlighted according to the
        # word list no. iQueryPart
        try:
            wf = word[u'wf']
        except:
            return False
##        if self.regexWf.match(wf) == None:
##            return False
        try:
            for wordToCheck in self.wordsToHighlight[iQueryPart][wf]:
                if self.obj_coincides(wordToCheck, word):
                    return True
        except KeyError:
            return False
        return False

    def word2text(self, word):
        try:
            text = word[u'wf']
        except KeyError:
            return u''
        bHighlight = self.check_word(word)
        if bHighlight:
            text = u'**' + text.upper() + u'**'
        return text

    def words2text(self, words):
        text = u''
        for i in range(len(words)):
            word = words[i]
            if i > 0 and (word[u'type'] == u'word' or\
                          word[u'wf'] in u'([<'):
                text += u' '
            text += self.word2text(word)
        text += u'\r\n'
        return text

    def highlight_words(self, words):
        text = u''
        for i in range(len(words)):
            bHighlight = self.check_word(words[i])
            if bHighlight:
                words[i][u'highlight'] = True
        return words
