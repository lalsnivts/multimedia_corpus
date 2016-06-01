# -*- coding: utf-8 -*-
__author__ = 'gisly'
import codecs
import json

def parse_json_file(text_filename_json):
    with codecs.open(text_filename_json, 'r', 'utf-8') as text_file_json:
        return json.loads(text_file_json.read())