# -*- coding: utf-8 -*-
__author__ = 'gisly'
import psycopg2
import file_utils
import common_constants

def import_text(text_filename_json, text_metadata):
    #TODO: parameterize
    #TODO: finally?
    conn = psycopg2.connect("dbname=multimedia_corpus user=postgres")
    cur = None
    try:
        cur = conn.cursor()
        multimedia_metadata, sentence_data = parse_text_data(text_filename_json)
        text_id = import_metadata(cur, text_metadata, multimedia_metadata)
        import_sentences(cur, text_id, sentence_data)
    finally:
        conn.commit()
        if cur is not None:
            cur.close()
            conn.close()
    
def import_metadata(cur, text_metadata, multimedia_metadata):
    multimedia_ids = load_multimedia(cur, multimedia_metadata)
    return load_text(cur, text_metadata, multimedia_ids)
    
def import_sentences(cur, text_id, sentence_data):
    for sentence in sentence_data:
        load_sentence(cur, sentence, text_id)
   
def load_text(cur, text_metadata, multimedia_ids):
    text_id = create_text(cur, text_metadata)
    for multimedia_id in multimedia_ids:
        create_text_multimedia_link(cur, text_id, multimedia_id)
    return text_id
        
def load_multimedia(cur, multimedia_metadata):
    multimedia_ids = []
    is_main = False
    main_multimedia_id = None
    for multimedia_type, multimedia_url in multimedia_metadata.iteritems():
        multimedia_id = create_multimedia(cur, multimedia_type, multimedia_url)
        if(multimedia_type == common_constants.FILE_TYPE_VIDEO) or (multimedia_type == common_constants.FILE_TYPE_AUDIO 
                                                   and main_multimedia_id is None):
            main_multimedia_id = multimedia_id
            is_main = True
        else:
            is_main = False
        multimedia_ids.append({'multimedia_id': multimedia_id, 'is_main': is_main})
    return multimedia_ids
        

def load_sentence(cur, sentence, text_id):
    sentence_id = create_sentence(cur, sentence, text_id)
    for word_order, word in enumerate(sentence['words']):
        load_word(cur, word, word_order, sentence_id)



def load_word(cur, word, word_order, sentence_id):
    word_id = create_word(cur, word, word_order, sentence_id)
    for morpheme_order, morpheme in enumerate(word['morphemes']):
        create_morpheme(cur, morpheme, morpheme_order, word_id)
        
def create_multimedia(cur, multimedia_type, multimedia_url):
    multimedia_query = "INSERT INTO multimedia_corpus.MULTIMEDIA(MULTIMEDIA_TYPE_ID, MULTIMEDIA_URL) VALUES (%s, %s) RETURNING MULTIMEDIA_ID"
    cur.execute(multimedia_query, (multimedia_type, multimedia_url))
    multimedia_id = cur.fetchone()[0]
    return multimedia_id

def create_text(cur, text_metadata):
    multimedia_query = "INSERT INTO multimedia_corpus.TEXTS(SPEAKER_ID, EXPEDITION_ID, PLACE_ID, LANGUAGE_ID)"\
                        "VALUES (%s, %s, %s, %s) RETURNING TEXT_ID"
    cur.execute(multimedia_query, (text_metadata['speakerId'], text_metadata['expeditionId'], 
                                   text_metadata['placeId'], text_metadata['languageId']))
    text_id = cur.fetchone()[0]
    return text_id

def create_text_multimedia_link(cur, text_id, multimedia_id):
    text_multimedia_query = "INSERT INTO multimedia_corpus.TEXTS_MULTIMEDIA(TEXT_ID, MULTIMEDIA_ID, IS_MAIN)"\
                        "VALUES (%s, %s, %s)"        
    cur.execute(text_multimedia_query, (text_id, multimedia_id['multimedia_id'], multimedia_id['is_main']))
    
def create_sentence(cur, sentence, text_id):
    sentence_query = "INSERT INTO multimedia_corpus.SENTENCES (TEXT_ID, MULTIMEDIA_START, MULTIMEDIA_END, ORIGINAL_TEXT, TRANSLATION_TEXT)"\
                    "VALUES (%s, %s, %s, %s, %s) RETURNING SENTENCE_ID"
    cur.execute(sentence_query, (text_id, sentence['start_ms'], sentence['stop_ms'], sentence['original'], sentence['rus']))
    sentence_id = cur.fetchone()[0]
    return sentence_id

def create_word(cur, word, word_order, sentence_id):
    word_query = "INSERT INTO multimedia_corpus.WORDS (SENTENCE_ID, WORD_ORDER, WORD_TRANSCRIPTION, POS_ID)"\
                "VALUES (%s, %s, %s, %s) RETURNING WORD_ID"
    cur.execute(word_query, (sentence_id, word_order, word['word'], None))
    word_id = cur.fetchone()[0]
    return word_id

def create_morpheme(cur, morpheme, morpheme_order, word_id):
    word_query = "INSERT INTO multimedia_corpus.MORPHEMES (WORD_ID, MORPHEME_ORDER, MORPHEME_TEXT, MORPHEME_TYPE, MORPHEME_GLOSS)"\
                "VALUES (%s, %s, %s, %s, %s) RETURNING MORPHEME_ID"
    cur.execute(word_query, (word_id, morpheme_order, morpheme['morpheme'], morpheme['morpheme_type'], morpheme['gl']))
    word_id = cur.fetchone()[0]
    return word_id
    



def parse_text_data(text_filename_json):
    text_json = file_utils.parse_json_file(text_filename_json)
    return {common_constants.FILE_TYPE_ELAN : text_json['original_filename'],
            common_constants.FILE_TYPE_AUDIO : text_json['audio'],
            common_constants.FILE_TYPE_VIDEO : text_json['video'],},\
            text_json['sentences']
    

import_text('ket/data/text_sentences.json', {'speakerId':1, 'expeditionId':1, 'placeId':1, 'languageId':2})
