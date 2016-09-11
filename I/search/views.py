# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.template import Template, Context
from django.template.loader import get_template
from django.http import HttpResponse
import json
from bson import json_util
import imp

import os

import datetime


search_platform_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'../search_platform/query_parser.py')
search_platform_path_multimedia = os.path.join(os.path.dirname(os.path.dirname(__file__)),'../search_platform/query_parser_multimedia.py')


query_parser = imp.load_source('query_parser',
                               search_platform_path)

query_parser_multimedia = imp.load_source('query_parser_multimedia',
                               search_platform_path_multimedia)

#qp = query_parser.QueryParser(u'yiddish')

qp_ket = query_parser_multimedia.QueryParserMultimedia()


TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

def search(request):
    errors = []
    form = {}
    if request.GET:
        form['search'] = request.GET.get('search')

        if not form['search']:
            errors.append('Введен пустой запрос')
             
        if not errors:
            # ... сохранение данных в базу
            return HttpResponse(json.dumps(request.GET))
    return render(request, 'search/search_multimedia.html', {'errors': errors, 'form':form})

def ex(request):
    query = {key: request.GET[key] for key in request.GET if len(request.GET[key]) > 0}
    coll = qp.search([query])
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
                      default=json_util.default)
                      # а вот так из этого делается json
    return HttpResponse(text)


def ket_ex(request):
    query = {key: request.GET[key] for key in request.GET if len(request.GET[key]) > 0}
    coll = qp_ket.search([query])
    print(coll)
    return render(request, 'search/search_multimedia_results.html', {'texts': coll})
