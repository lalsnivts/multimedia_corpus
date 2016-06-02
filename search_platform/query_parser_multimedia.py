# -*- coding: utf-8 -*-
__author__ = 'gisly'
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from db_client_multimedia import DBClientMultimedia

class QueryParserMultimedia:
    def __init__(self):
        self.db_client = DBClientMultimedia()
    def search(self, query):
        print("query_parser")
        result_db = self.db_client.search(query[0])
        
        result_grouped  = []
        cur_text = None
        cur_sentence = None
        cur_word = None
        for result in result_db:
            if cur_text is None or result['text_id'] != cur_text['text_id']:
                if cur_text:
                    result_grouped.append(cur_text)
                cur_text = dict()
                cur_text['text_id'] = result['text_id']
                cur_text['name'] = result['name']
                cur_text['patronymic'] = result['patronymic']
                cur_text['surname'] = result['surname']
                cur_text['sentences'] = []
                cur_text['multimedia'] = []
                cur_text['multimedia_ids'] = set()
                
            if result['multimedia_id'] not in cur_text['multimedia_ids']:
                cur_text['multimedia'].append({'type':result['multimedia_type'], 'url': result['multimedia_url']})
                cur_text['multimedia_ids'].add(result['multimedia_id']) 
        
            #the multimedia data repeats for each row
            #so we only process the data for a single multimedia_row
            if len(cur_text['multimedia_ids']) >= 2:
                continue
            
            if result['multimedia_id'] not in cur_text['multimedia_ids']:
                cur_text['multimedia'].append({'type':result['multimedia_type'], 'url': result['multimedia_url']})
                cur_text['multimedia_ids'].add(result['multimedia_id'])
                
                
                
            if cur_sentence is None or result['sentence_id'] != cur_sentence['sentence_id']:
                if cur_sentence:
                    cur_text['sentences'].append(cur_sentence)
                cur_sentence = dict()
                cur_sentence['sentence_id'] = result['sentence_id']
                cur_sentence['original_text'] = result['original_text']
                cur_sentence['translation_text'] = result['translation_text']
                cur_sentence['words'] = []
            if cur_word is None or result['word_id'] != cur_word['word_id']:
                if cur_word:
                    cur_sentence['words'].append(cur_word)
                cur_word = dict()
                cur_word['word_id'] = result['word_id']
                cur_word['sentence_word'] = dict()
                cur_word['sentence_word']['transcription'] = result['sentence_word']
                if result.get('found_word') and result['sentence_word'] == result['found_word']:
                    cur_word['sentence_word']['is_found'] = 1  
                cur_word['morphemes'] = []
                    
            morpheme = dict()
            morpheme['morpheme'] = dict()
            morpheme['morpheme']['text'] = result['word_morpheme_text']
            morpheme['morpheme']['gloss'] = result['word_morpheme_gloss']
            if result.get('found_morpheme_text') and result['word_morpheme_text'] == result['found_morpheme_text']:
                    morpheme['morpheme']['is_found'] = 1  
            cur_word['morphemes'].append(morpheme)
            
            
        
        if cur_text and cur_sentence and cur_word:
            cur_sentence['words'].append(cur_word)
            cur_text['sentences'].append(cur_sentence)       
            
            result_grouped.append(cur_text)
            
        return result_grouped
            
        
qp = QueryParserMultimedia()
print(qp.search([{'sen.translation_text':u'Привет, как дела?', 'w.word_transcription':u'привет'}]))
            
    

