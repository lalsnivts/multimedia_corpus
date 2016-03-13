import os, codecs, re, json
projectName = u'yiddish'

class XMLReader:
    def __init__(self,\
                 conf_path=os.path.join(projectName, u'conf'),
                 data_path=os.path.join(projectName, u'data'),
                 meta_path=os.path.join(projectName, u'meta'),
                 meta_sep=u'\t'):
        self.punc = u'[\\.,:;"\'@?!()\\[\\]8%\\^&$/\\-+=~`«»§¡‒–—―‘’‚‛“”„‟‰_]'
        self.conf_path = conf_path
        self.data_path = data_path
        self.meta_path = meta_path
        self.load_categories(os.path.join(conf_path,\
                                                            u'categories.json'))
        self.load_meta(os.path.join(meta_path, u'meta.csv'), meta_sep)


    def load_categories(self, fname):
        fCategories = codecs.open(fname, 'r', 'utf-8')
        self.categories = json.loads(fCategories.read())
        fCategories.close()


    def load_meta(self, fname, meta_sep=u'\t'):
        fMeta = codecs.open(fname, 'r', 'utf-8')
        self.meta = {}
        for line in fMeta:
            try:
                name, title, author, date_since,\
                      date_till, genres = line.strip().split(meta_sep, 6)
            except:
                print u'Error in meta: ' + line
                continue
            metadata = {u'title': title, u'author': author,\
                        u'date_since': self.date_unpack(date_since),\
                        u'date_till': self.date_unpack(date_till),\
                        u'genres': list(genres.split(u' '))}
            self.meta[name.lower()] = metadata
        fMeta.close()


    def find_meta(self, fname):
        fnameOrig = fname
        fname = re.sub(u'^\\.[/\\\\]|(?:-processed)?\\.[^.]*$', u'',\
                       fname.lower())
        try:
            dictMeta = self.meta[fname]
        except KeyError:
            try:
                fname = re.sub(u'^.*[/\\\\]([^/\\\\]+)$', u'\\1', fname)
                dictMeta = self.meta[fname]
            except KeyError:
                print u'No metadata for ' + fnameOrig + u'.'
                dictMeta = {}
        dictMeta[u'filename'] = fnameOrig
        return dictMeta
    

    def date_unpack(self, date):
        dictDate = {}
        fields = re.findall(u'[^.]+', date)
        try:
            if len(fields) >= 1:
                dictDate[u'year'] = int(fields[0])
            if len(fields) >= 2:
                dictDate[u'month'] = int(fields[1])
            if len(fields) >= 3:
                dictDate[u'day'] = int(fields[2])
        except:
            return {}
        return dictDate
    
        
    def gram_dict(self, gr):
        values = gr.split(u',')
        dictGr = {}
        for v in values:
            v = v.strip()
            try:
                dictGr[self.categories[v]] = v
            except:
                pass
        return dictGr


    def attributes_dict(self, s):
        kvPairs = re.findall(u'([\\w\\d_\\-]+)\\s*=\\s*"([^"]*)"',\
                             s, flags=re.U)
        dictRest = {}
        for pair in kvPairs:
            dictRest[pair[0]] = pair[1]
        return dictRest


    def separate_ana(self, ana):
        m_ana = re.match(u'^\\s*lex\\s*=\\s*"([^"]*)"\\s*'
                         u'gr\\s*=\\s*"([^"]*)"\\s*([^>]*)></ana.*$', ana)
        lex = m_ana.group(1)
        if lex == None:
            lex = u''
        gr = m_ana.group(2)
        if gr == None:
            gr = u''
        gr = re.sub(u'\\s+', u'', gr)
        gr = re.sub(u'\\.{2,}', u'.', gr)
        gr = re.sub(u',{2,}', u',', gr)
        gr = gr.replace(u'.', u',')
        rest = m_ana.group(3)
        return lex, gr, rest


    def get_word(self, line):
        m = re.search(u'^(<ana.*>)([^<>]+?)\\s*$', line)
        if m == None:
            return []
        analyses = m.group(1)
        wf = m.group(2)
        list_analyses = set([self.separate_ana(ana)\
                             for ana in re.split(u'\\s*<ana\\s*', analyses)\
                             if len(ana) > 5])
        listDictAnalyses = []
        for ana in sorted(list_analyses, key = lambda x: x[0]):
            lex, gr, rest = ana
            dictAnalysis = {u'lex': lex}
            dictGr = self.gram_dict(gr)
            dictAnalysis[u'gr'] = dictGr
            dictAnalysis.update(self.attributes_dict(rest))
            listDictAnalyses.append(dictAnalysis)
        word = {u'wf': wf,\
                u'ana': listDictAnalyses,\
                u'type': u'word'}
        return [word]


    def get_words(self, line):
        words = []
        numWords = 0
        bLastInSent = False
        if u'<w>' not in line:
            wfs = re.findall(u'\\.\\.\\.|\\?!|' + self.punc +
                             u'|[\\w\\-]+',\
                             line, flags=re.U)
            for wf in wfs:
                if re.search(u'\\w', wf, flags=re.U) != None:
                    wfType = u'word'
                    numWords += 1
                else:
                    wfType = u'punc'
                    # includes Greek question mark
                    if re.search(u'[.?!;]', wf) != None:
                        bLastInSent = True
                word = {u'wf': wf,\
                        u'type': wfType}
                words.append(word)
        else:
            wfs = re.findall(u'(' + self.punc + u'*)\\s*<w>(.*?)</w>\\s*(' +\
                             self.punc + u'*)\\s*', line, flags=re.U)
            for wf in wfs:
                numWords += 1
                for symbol in wf[0]:
                    word = {u'wf': symbol,\
                            u'type': u'punc'}
                    words.append(word)
                words += self.get_word(wf[1])
                if re.search(u'[.?!;]', wf[2]) != None:
                   bLastInSent = True
                for symbol in wf[2]:
                    word = {u'wf': symbol,\
                            u'type': u'punc'}
                    words.append(word)
        
        return words, numWords, bLastInSent


    def process_text(self, fname):
        f = codecs.open(fname, 'r', 'utf-8')
        sentences = []
        curSentence = []
        iWords = 0
        dictMeta = self.find_meta(fname)
        print u'Processing ' + fname
        for line in f:
            line = line.strip()
            ## AD HOC FOR GREEK!
            line = line.replace(u'transl-en', u'transl_en')
            if re.search(u'^<(?:/?(?:body|html|head|p))>$', line) != None:
                continue
            words, numWords, lastInSentence = self.get_words(line)
            iWords += numWords
            curSentence += words
            if lastInSentence:
                sentences.append({u'words': curSentence[:],\
                                  u'doc': fname})
                curSentence = []
        f.close()
        if len(curSentence) > 0:
            sentences.append({u'words': curSentence[:],\
                              u'doc': fname})
        dictMeta[u'sentences'] = len(sentences)
        dictMeta[u'words'] = iWords
        return sentences, dictMeta


    def process_dir(self, dirname):
        sentences = []
        metaOut = []
        for root, dirs, files in os.walk(dirname):
            for fname in files:
                if re.search(u'\\.x(?:ht)?ml', fname) == None:
                    continue
                newSentences, newMeta =\
                              self.process_text(os.path.join(root, fname))
                sentences += newSentences
                metaOut.append(newMeta)
        return sentences, metaOut


    def write_data(self, sentences, meta):
        print u'docs: ' + str(len(meta))
        fDocs = codecs.open(os.path.join(self.data_path, u'docs.json'),\
                            'w', 'utf-8')
        fDocs.write(json.dumps(meta, ensure_ascii=False))
        fDocs.close()
        print u'sentences: ' + str(len(sentences))
        fS = codecs.open(os.path.join(self.data_path, u'sentences.json'),\
                         'w', 'utf-8')
        fS.write(json.dumps(sentences, ensure_ascii=False))
        fS.close()


if __name__ == u'__main__':
    reader = XMLReader()
    sentences, meta = reader.process_dir(u'./test_texts')
    reader.write_data(sentences, meta)


