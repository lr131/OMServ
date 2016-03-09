# -*- coding: utf-8 -*-
#


from flask import render_template
from app import app
from smartcard.System import readers
from smartcard.scard import *
import smartcard.util
import json

def bcd_to_int(bcd):
    """Decode a 2x4bit BCD to a integer.
    """
    out = 0
    for d in (bcd >> 4, bcd):
        for p in (1, 2, 4 ,8):
            if d & 1:
                out += p
            d >>= 1
        out *= 10
    return out / 10


def find2elements(data, arg1, arg2):
    count_list = len(data)
    i = 1
    index = -1
    while i < count_list:
        if data[i-1] == arg1 and data[i] == arg2:
            index = i
            break
        i = i+1
    return index


def read_tag(data, *tags):
    index = find2elements(data, tags[0], tags[1]);
    if index == -1:
        return None
    tagoflength = index+1
    startreadtag = index+2
    endreadtag = tagoflength+data[tagoflength]
    if data[tagoflength] == 1:
        if data[startreadtag] == 1:
            zn1 = True
        else:
            zn1 = False
    if data[tagoflength] == 4:
        zn1 = str(bcd_to_int(data[startreadtag+2])).zfill(2)+str(bcd_to_int(data[startreadtag+3])).zfill(2)+'-'+str(bcd_to_int(data[startreadtag+1])).zfill(2)+'-'+str(bcd_to_int(data[startreadtag])).zfill(2)
    if data[tagoflength] != 1 and data[tagoflength] != 4:
        zn1 = bytearray(data[startreadtag:endreadtag+1]).decode('utf8')
    print zn1
    return (zn1)


@app.route('/')
@app.route('/index')
def index():
    user = { 'nickname': 'Miguel' }
    posts = [
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    answer = {}.fromkeys(['ok', 'msg', 'data'])
    dict_data = {}.fromkeys(['pol_ser', 'pol_num', 'policy', 'family', 'name', 'patr', 'sex', 'bdate', 'country_code', 'country', 'snils', 'dataend', 'bplace', 'data_make_oms', 'fimg', 'img', 'ogrn', 'okato', 'data_start_insurance', 'data_end_insurance'])
    r = readers()
    try:
        reader = r[0]
        connection = reader.createConnection()
        try:
            connection.connect()
            SELECT_DIR_CONST =  [0x00, 0xa4, 0x04, 0x0c, 0x07, 0x46, 0x4f, 0x4d, 0x53, 0x5f, 0x49, 0x44]
            SELECT_FILE_CONST = [0x00, 0xa4, 0x02, 0x0c, 0x02, 0x02, 0x01]
            READ_FILE_CONST = [0x00, 0xb0, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(SELECT_DIR_CONST)
            if sw1 != 144 and sw2 != 0:
                answer['ok'] = 0
                if sw1 == 0x6a:
                    answer['msg'] = u'Карта не поддерживается'
                    print answer['msg']
                else:
                    answer['msg'] = u'Неизвестная ошибка'
                    print answer['msg']
                raise SystemExit
            data, sw1, sw2 = connection.transmit(SELECT_FILE_CONST)
            data_const, sw1, sw2 = connection.transmit(READ_FILE_CONST)
            SELECT_DIR_CHANGE =  [0x00, 0xa4, 0x04, 0x0c, 0x07, 0x46, 0x4f, 0x4d, 0x53, 0x5f, 0x49, 0x4e, 0x53]
            READ_DIR_CHANGE = [0x00, 0xca, 0x01, 0xb0, 0x02] 
            data, sw1, sw2 = connection.transmit(SELECT_DIR_CHANGE)
            data, sw1, sw2 = connection.transmit(READ_DIR_CHANGE) 
            SELECT_FILE_CHANGE = [0x00, 0xa4, 0x02, 0x0c, 0x02]
            SELECT_FILE_CHANGE.append(data[0])
            SELECT_FILE_CHANGE.append(data[1])
            data, sw1, sw2 = connection.transmit(SELECT_FILE_CHANGE)
            READ_FILE_CHANGE = [0x00, 0xb0, 0x00, 0x00, 0x00]
            data_change, sw1, sw2 = connection.transmit(READ_FILE_CHANGE)
            dict_data = {
                'pol_ser': None,
                'pol_num': read_tag(data_const, 0x5f, 0x26),
                'policy': read_tag(data_const, 0x5f, 0x26),
                'family': read_tag(data_const, 0x5f, 0x21),
                'name': read_tag(data_const, 0x5f, 0x22),
                'patr': read_tag(data_const, 0x5f, 0x23),
                'sex': read_tag(data_const, 0x5f, 0x25),
                'bdate': read_tag(data_const, 0x5f, 0x24),
                'country_code': read_tag(data_const, 0x5f, 0x31),
                'country': read_tag(data_const, 0x5f, 0x32),
                'snils': read_tag(data_const, 0x5f, 0x27),
                'dataend': read_tag(data_const, 0x5f, 0x28),
                'bplace': read_tag(data_const, 0x5f, 0x29),
                'data_make_oms': read_tag(data_const, 0x5f, 0x2a),
                'fimg': read_tag(data_const, 0x5f, 0x41),
                'img': read_tag(data_const, 0x5f, 0x42),
                'ogrn': read_tag(data_change, 0x5f, 0x51),
                'okato': read_tag(data_change, 0x5f, 0x52),
                'data_start_insurance': read_tag(data_change, 0x5f, 0x53),
                'data_end_insurance': read_tag(data_change, 0x5f, 0x54)
                #'ecp': read_tag(data_change, 0x5f, 0x61)
                }
            answer['ok'] = 1
            answer['msg'] = u'Успешно'
            answer['data'] = dict_data 
        except smartcard.Exceptions.CardConnectionException:
            answer['ok'] = 0
            answer['msg'] = u'Проверьте карту'
            
    except IndexError:
        answer['ok'] = 0
        answer['msg'] = u'Подключите считыватель'
    finally:
        datajs = json.dumps(answer, sort_keys=True),
        return render_template("index.html", 
            ok = answer['ok'],
            msg = answer['msg'],
            data = dict_data
            )
