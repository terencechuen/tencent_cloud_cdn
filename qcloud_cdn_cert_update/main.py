# -*- coding: UTF-8 -*-

import base64
import json
import os
import re
import sys

import OpenSSL
import chardet
from QcloudApi.qcloudapi import QcloudApi

config_file_path = sys.path[0] + '/config_private.json'
tmp_file_path = sys.path[0] + '/temp.log'
cert_file_folder = sys.path[0] + '/cert/'


def format_config_file():
    if os.path.exists(config_file_path):
        r = open(config_file_path, 'r')
        c_json = json.load(r)
        r.close()
        return c_json
    else:
        return False


if format_config_file() is False:
    print('file config.json config error, script exit!')
    sys.exit(0)
else:
    config_json = format_config_file()


def check_cert_subjectaltname(cert_file_path):
    r = open(cert_file_path, 'r')
    r_content = r.read().encode()
    r.close()
    cert_type = OpenSSL.crypto.FILETYPE_PEM
    i = OpenSSL.crypto.load_certificate(cert_type, r_content)
    i_count = i.get_extension_count()
    dns_name = ''
    for j in range(i_count):
        k = i.get_extension(j)
        k_name = k.get_short_name()
        if k_name.decode() == 'subjectAltName':
            dns_name = k
    dns_name = dns_name.get_data()
    dns_name_chardet = chardet.detect(dns_name)
    dns_name = dns_name.decode(dns_name_chardet['encoding'])
    dns_name = re.sub(r'[^\S]', '', dns_name).split('‚')
    return dns_name


def format_cert_key(i):
    crt_file_path = cert_file_folder + i + '.crt'
    key_file_path = cert_file_folder + i + '.key'
    if os.path.exists(crt_file_path):
        r = open(crt_file_path, 'r')
        r_content = r.read()
        r.close()
        crt_base64 = base64.encodebytes(r_content.encode()).decode()
    else:
        print('cert error, script exit!')
        sys.exit(0)
    if os.path.exists(key_file_path):
        r = open(key_file_path, 'r')
        r_content = r.read()
        r.close()
        key_base64 = base64.encodebytes(r_content.encode()).decode()
    else:
        print('key error, script exit!')
        sys.exit(0)
    output_dict = dict()
    output_dict['crt'] = crt_base64
    output_dict['key'] = key_base64
    return output_dict


for key, value in config_json.items():
    print(key)
    print(value)
    config = {
        'secretId': value['secret_id'],
        'secretKey': value['secret_key'],
    }
    crt_key_dict = format_cert_key(key)
    action = value['action']
    module = value['module']
    params = {
        'host': key,
        'httpsType': value['https_type'],
        'forceSwitch': value['https_force_switch'],
        'http2': value['http2'],
        'cert': crt_key_dict['crt'],
        'privateKey': crt_key_dict['key']
    }
    service = QcloudApi(module, config)
    print(service.generateUrl(action, params))
    # qcloud_output = service.call(action, params).decode()

    # print(qcloud_output)
