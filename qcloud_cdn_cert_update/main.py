# -*- coding: UTF-8 -*-

import json
import os
import sys
import base64

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
    secret_id = config_json['secret_id']
    secret_key = config_json['secret_key']


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


# 模块
module = 'cdn'

# 接口
action = 'SetHttpsInfo'

host_name = 'cdn.enginx.cn'
https_type = 2
https_force_switch = 2
http2 = 'on'

config = {
    'secretId': secret_id,
    'secretKey': secret_key,
}

crt_key_dict = format_cert_key(host_name)

params = {
    'host': host_name,
    'httpsType': https_type,
    'forceSwitch': https_force_switch,
    'http2': http2,
    'cert': crt_key_dict['crt'],
    'privateKey': crt_key_dict['key']
}

service = QcloudApi(module, config)
# print(service.generateUrl(action, params))
qcloud_output = service.call(action, params).decode()

print(qcloud_output)
