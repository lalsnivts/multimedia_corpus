# -*- coding: utf-8 -*-
__author__ = 'gisly'
import psycopg2
import psycopg2.extras

class DBClientMultimedia:
    conn = None
    
    query_select = "select t.text_id, s.name, s.patronymic, s.surname, "\
                    "sen.sentence_id, sen.multimedia_start, sen.multimedia_end, "\
                    "sen.original_text, sen.translation_text"
                    
    query_select_word = "w.word_transcription as sentence_word"
    query_select_all_words = "w.word_transcription as found_word, w2.word_transcription as sentence_word"
    
    query_from =  "from multimedia_corpus.texts t "\
                    "join multimedia_corpus.speakers s on s.speaker_id = t.speaker_id "\
                    "join multimedia_corpus.sentences sen on t.text_id = sen.text_id "\
                    "join multimedia_corpus.words w on sen.sentence_id = w.sentence_id"
    query_from_all_words = "multimedia_corpus.words w2"
    
    query_condition_all_words = "w2.sentence_id = w.sentence_id"
           
    query_order_group = " order by t.text_id, sen.sentence_id, w.word_order"
    query_order_all_words = "w2.word_order"

    def __init__(self):
        #TODO: db settings!
        #TODO: logging
        self.conn = psycopg2.connect("dbname=multimedia_corpus user=postgres")
        #TODO: close connection!
        
    def search(self, query):
        query_string, parameters = self.construct_query_string(query)
        cur = self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        
        cur.execute(query_string, parameters)
        result_tuples = cur.fetchall()
        cur.close()
        result_by_columns = []
        for result_tuple in result_tuples:
            result_by_columns.append(dict(result_tuple))
        
        return result_by_columns
        
    def construct_query_string(self, query):
        #TODO: check the fiels
        condition = ""
        parameters = []
        for key, value in query.iteritems():
            if value != "":
                condition += " and " + key + " = %s" 
                parameters.append(value)
        parameters = tuple(parameters)
        condition = condition.strip(" and ")
        
        print(condition)
        query_string = self.query_select
        
        is_word_query = self.is_word_query(query)
        if is_word_query:
            query_string += ', ' + self.query_select_all_words + " " + self.query_from + "," + self.query_from_all_words
        else:  
            query_string += ', ' + self.query_select_word + " " + self.query_from
        
        
        
        if condition != "":
            query_string += " where " + condition
        
        if is_word_query:
            if condition == "":
                query_string += " where "
            else:
                query_string += " and "
            query_string += self.query_condition_all_words
                    
        
        query_string +=  self.query_order_group
        if is_word_query:
            query_string +=  "," + self.query_order_all_words
        
        print(query_string)
        return query_string, parameters
    
    def is_word_query(self, query):
        return 'w.word_transcription' in query