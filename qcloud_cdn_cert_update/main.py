# -*- coding: UTF-8 -*-

import base64
import json
import re
import sys

import OpenSSL
import chardet
from QcloudApi.qcloudapi import QcloudApi

config_file_path = sys.path[0] + '/config_private.json'
tmp_file_path = sys.path[0] + '/temp.log'
cert_file_folder = sys.path[0] + '/cert/'


def try_to_open_file(file_path):
    try:
        open_file = open(file_path, 'r')
    except IOError as e:
        print(e)
        sys.exit(0)
    else:
        read_file = open_file.read()
        open_file.close()
        return read_file


def check_cert_info(cert_file_path):
    output_dict = dict()

    crt_content = try_to_open_file(cert_file_path).encode()
    cert_type = OpenSSL.crypto.FILETYPE_PEM
    j = OpenSSL.crypto.load_certificate(cert_type, crt_content)

    output_dict['crt_not_before'] = j.get_notBefore().decode()
    output_dict['crt_not_after'] = j.get_notAfter().decode()

    j_count = j.get_extension_count()
    dns_name = ''
    for f in range(j_count):
        k = j.get_extension(f)
        k_name = k.get_short_name()
        if k_name.decode() == 'subjectAltName':
            dns_name = k
    dns_name = dns_name.get_data()
    dns_name_chardet = chardet.detect(dns_name)
    dns_name = dns_name.decode(dns_name_chardet['encoding'])
    dns_name = re.sub(r'[^\S]', '', dns_name).split('‚')
    output_dict['dns_name'] = dns_name
    return output_dict


def format_cert_key(domain_name):
    crt_file_path = cert_file_folder + domain_name + '.crt'
    key_file_path = cert_file_folder + domain_name + '.key'

    if domain_name in check_cert_info(crt_file_path)['dns_name']:
        crt_content = try_to_open_file(crt_file_path)
        crt_base64 = base64.encodebytes(crt_content.encode()).decode()

        key_content = try_to_open_file(key_file_path)
        key_base64 = base64.encodebytes(key_content.encode()).decode()

        output_dict = dict()
        output_dict['crt'] = crt_base64
        output_dict['key'] = key_base64
        return output_dict
    else:
        return False


config_json = json.loads(try_to_open_file(config_file_path))

for key, value in config_json.items():
    crt_key_dict = format_cert_key(key)

    if crt_key_dict is False:
        continue
    else:
        config = {
            'secretId': value['secret_id'],
            'secretKey': value['secret_key'],
        }
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
