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
            if cur_sentence is None or result['sentence_id'] != cur_sentence['sentence_id']:
                if cur_sentence:
                    cur_text['sentences'].append(cur_sentence)
                cur_sentence = dict()
                cur_sentence['sentence_id'] = result['sentence_id']
                cur_sentence['original_text'] = result['original_text']
                cur_sentence['translation_text'] = result['translation_text']
                cur_sentence['words'] = []
            word = dict()
            word['sentence_word'] = dict()
            word['sentence_word']['transcription'] = result['sentence_word']
            if result.get('found_word') and result['sentence_word'] == result['found_word']:
                word['sentence_word']['is_found'] = 1
            cur_sentence['words'].append(word)
            
                
        if cur_text and cur_sentence:
            cur_text['sentences'].append(cur_sentence)       
            result_grouped.append(cur_text) 
        return result_grouped
            
        
qp = QueryParserMultimedia()
print(qp.search([{'sen.translation_text':u'Привет, как дела?', 'w.word_transcription':u'привет'}]))
            
    

