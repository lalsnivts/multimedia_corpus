# -*- coding: utf-8 -*-

import logging as l
import xml.etree.ElementTree as ET
import json

l.basicConfig(level=l.INFO)

def load_tier(tree, tierId):
    l.info('Load TIER with id = %s ' % tierId)
    xpath = './/TIER[@TIER_ID=\'%s\']' % tierId

    return tree.find(xpath)

def _load_simple_ref_tier(tree, name):
    tier = load_tier(tree, name)

    result = {}
    for elt in tier.findall('.//REF_ANNOTATION'):
        id = elt.get('ANNOTATION_ID')

        if id in result:
            l.error('Duplicate ANNOTATION_ID (%s) in \"%s\" TIER' % id, name)

        result[id] = {
            'ref_id': elt.get('ANNOTATION_REF'),
            'value': elt[0].text
        }

    return result

def _reverse_simple_ref_dict(dict):
    result = {}

    for id, data in dict.iteritems():
        ref_id = data['ref_id']
        new_data = data.copy()
#        new_data['id'] = id

        if ref_id not in result:
            result[ref_id] = [new_data]
        else:
            result[ref_id].append(new_data)

    return result

def _reverse_simple_ref_dict_distinct(dict):
    result = {}

    for id, data_list in _reverse_simple_ref_dict(dict).iteritems():
        if len(data_list) <> 1:
            l.error("Data list size <> 1")

        result[id] = data_list[0].copy()

    return result

def load_translation_sentences(tree):
    return _load_simple_ref_tier(tree, 'rus')

def load_morphemes_tier(tree):
    return _load_simple_ref_tier(tree, 'gl')

def load_fon(tree, morphemesTier):
    morphemesTier = _reverse_simple_ref_dict(morphemesTier)
    result = _load_simple_ref_tier(tree, 'fon')

    for id, data in result.iteritems():
        morphemes = []

        for m in morphemesTier[id]:
            morphemes.append(m['value'])

        data['morphemes'] = morphemes

    return result

def load_time_order(tree):
    result = {}

    for elt in tree.findall(".//TIME_ORDER/TIME_SLOT"):
        id = elt.get('TIME_SLOT_ID')

        if id in result:
            l.error('Duplicate TIME_SLOT_ID (%s) in TIME_ORDER' % id)

        result[id] = elt.get('TIME_VALUE')

    return result

def load_orig_sentences(tree, timeOrder, translationTier, wordsTier):
    translationTier = _reverse_simple_ref_dict_distinct(translationTier)
    tier = load_tier(tree, 'ket')

    result = {}
    for elt in tier.findall('.//ALIGNABLE_ANNOTATION'):
        id = elt.get('ANNOTATION_ID')

        if id in result:
            l.error('Duplicate ANNOTATION_ID (%s) in ket tier' % id)

        result[id] = {
            'start_time': timeOrder[elt.get('TIME_SLOT_REF1')],
            'stop_time': timeOrder[elt.get('TIME_SLOT_REF2')],
            'original': elt[0].text,
            'rus': translationTier[id]['value'],
            'words': wordsTier[id],
        }

    return result

def _cmp_sent(a, b):
    if a['prev_id'] is None and b['prev_id'] is None: return 0
    if a['prev_id'] is None: return -1
    if b['prev_id'] is None: return 1

    return cmp(a['prev_id'], b['prev_id'])

def load_words(tree, fonTier):
    tier = load_tier(tree, 'fonWord')
    fonTier = _reverse_simple_ref_dict(fonTier)

    sent_dict = {}
    for elt in tier.findall('.//REF_ANNOTATION'):
        id = elt.get('ANNOTATION_ID')

        sent_ref_id = elt.get('ANNOTATION_REF')
        prev_id = elt.get('PREVIOUS_ANNOTATION')
        value = elt[0].text

        sent_data = {
            'id': id,
            'value': value,
            'prev_id': prev_id,
        }

        if sent_ref_id not in sent_dict:
            sent_dict[sent_ref_id] = [sent_data]
        else:
            sent_dict[sent_ref_id].append(sent_data)

    for id, data_list in sent_dict.iteritems():
        data_list = sorted(data_list, _cmp_sent)

        for data in data_list:
            data.pop('prev_id')
            data['fon'] = fonTier[data['id']]

#       changed: added
        for data in data_list:
            data.pop('id')

    return sent_dict


xml_file_path = 'ket/data/Kel05_AbdullaevaEP_bear.eaf'
tree = ET.parse(xml_file_path)

time_order = load_time_order(tree)
morpheme_tier = load_morphemes_tier(tree)
fon_tier = load_fon(tree, morpheme_tier)
words_tier = load_words(tree, fon_tier)

rus_tier = load_translation_sentences(tree)
ket_tier = load_orig_sentences(tree, time_order, rus_tier, words_tier)

print json.dumps(
    ket_tier,
    sort_keys=True, indent = 4, separators = (',', ': ')
    ,ensure_ascii = False
).encode('utf-8')

