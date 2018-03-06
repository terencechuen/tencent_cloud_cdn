# -*- coding: UTF-8 -*-

import base64
import json
import re
import sys
from datetime import datetime
import OpenSSL
import chardet
from QcloudApi.qcloudapi import QcloudApi

# 配置文件、日志路径与证书文件夹
config_file_path = sys.path[0] + '/config_private.json'
tmp_file_path = sys.path[0] + '/temp.log'
cert_file_folder = sys.path[0] + '/cert/'


# 读取文件的通用函数
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


# 查找证书的有效期、生效时间
# 查找证书中包含的所有域名
def check_cert_info(cert_file_path):
    output_dict = dict()

    # 读取证书内容
    crt_content = try_to_open_file(cert_file_path).encode()
    # 定义证书格式
    cert_type = OpenSSL.crypto.FILETYPE_PEM
    # 加载证书
    j = OpenSSL.crypto.load_certificate(cert_type, crt_content)

    # 获取证书生效时间，写入到字典以备输出
    output_dict['crt_not_before'] = j.get_notBefore().decode()
    # 获取证书失效时间，写入到字典以备输出
    output_dict['crt_not_after'] = j.get_notAfter().decode()

    # 统计证书拓展字段数量
    j_count = j.get_extension_count()
    dns_name = ''

    # 遍历拓展，寻找名为subjectAltName的字段
    for f in range(j_count):
        k = j.get_extension(f)
        k_name = k.get_short_name()
        if k_name.decode() == 'subjectAltName':
            dns_name = k
    # 从subjectAltName字段中提取域名，以列表保存并写入到字典以备输出
    dns_name = dns_name.get_data()
    dns_name_chardet = chardet.detect(dns_name)
    dns_name = dns_name.decode(dns_name_chardet['encoding'])
    dns_name = re.sub(r'[^\S]', '', dns_name).split('‚')
    output_dict['dns_name'] = dns_name
    return output_dict


# 检查证书是否已生效
# 检查证书是否已过期
# 检查目标域名是否在该证书中
def format_cert_key(domain_name, crt_file_name, key_file_name):
    crt_file_path = cert_file_folder + crt_file_name
    key_file_path = cert_file_folder + key_file_name

    check_cert_info_dict = check_cert_info(crt_file_path)

    # 判断域名是否在该证书中
    if domain_name in check_cert_info_dict['dns_name']:
        # 获取本地UTC时间
        datetime_now = datetime.utcnow()

        # 将字符串解析为时间元组
        crt_not_before = datetime.strptime(check_cert_info_dict['crt_not_before'], '%Y%m%d%H%M%SZ')
        crt_not_after = datetime.strptime(check_cert_info_dict['crt_not_after'], '%Y%m%d%H%M%SZ')

        # 如果现在的时间大于证书生效时间，则为True
        if datetime_now >= crt_not_before:
            # 如果证书失效时间-现在的时间大于配置文件中validity（单位：天）的值，则为True
            if (crt_not_after - datetime_now).days >= int(config_json[domain_name]['validity']):
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
        else:
            return False


# 载入配置文件
config_json = json.loads(try_to_open_file(config_file_path))

# 遍历字典
for key, value in config_json.items():
    # 如果cert_filename为空，则将证书文件名为默认的[domain_name].crt
    # 否则则加载配置文件中的文件名
    if value['cert_filename'] == "":
        cert_filename = key + '.crt'
    else:
        cert_filename = value['cert_filename']

    # 如果cert_filename为空，则将证书文件名为默认的[domain_name].key
    # 否则则加载配置文件中的文件名
    if value['key_filename'] == "":
        key_filename = key + '.key'
    else:
        key_filename = value['key_filename']

    # 调用函数，检查证书是否合规
    crt_key_dict = format_cert_key(key, cert_filename, key_filename)

    # 不合规则跳过，进入下一循环
    if crt_key_dict is False:
        continue
    else:
        # 腾讯云基础设定
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
        # 调用API
        service = QcloudApi(module, config)
        # 可输出编码后的URL，主要用于日志，也可以生成URL后手动执行
        # 自动化应用一般不需要
        # print(service.generateUrl(action, params))
        # 执行API
        qcloud_output = service.call(action, params).decode()
        # print(qcloud_output)
