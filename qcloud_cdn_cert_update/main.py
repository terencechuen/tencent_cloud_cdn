# -*- coding: UTF-8 -*-

import base64
import json
import sys
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from QcloudApi.qcloudapi import QcloudApi

# 配置文件、日志路径与证书文件夹
config_file_path = sys.path[0] + '/config.json'
tmp_file_path = sys.path[0] + '/temp.log'
cert_file_folder = sys.path[0] + '/cert/'


# 读取文件的通用函数
def try_to_open_file(file_path, exit_type):
    try:
        open_file = open(file_path, 'r')
    except Exception as e:
        if exit_type == 0:
            return False, e
        else:
            print(e)
            sys.exit(0)
    else:
        read_file = open_file.read()
        open_file.close()
        return True, read_file


# 载入配置文件
config_json = json.loads(try_to_open_file(config_file_path, 1)[1])


# 查找证书的有效期、生效时间
# 查找证书中包含的所有域名
def check_cert_info(cert_file_path):
    crt_open = open(cert_file_path, 'r')
    crt_content = crt_open.read()
    crt_open.close()

    crt = x509.load_pem_x509_certificate(crt_content.encode(), default_backend())

    # 获取证书序列号
    crt_serial_number = crt.serial_number

    # 获取alt name
    crt_altname = crt.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    crt_altname = crt_altname.value.get_values_for_type(x509.DNSName)

    # 获取生效时间
    crt_not_valid_before = crt.not_valid_before
    # 获取过期时间
    crt_not_valid_after = crt.not_valid_after

    crt_output = dict()
    crt_output['crt_altname'] = crt_altname
    crt_output['crt_not_valid_before'] = crt_not_valid_before
    crt_output['crt_not_valid_after'] = crt_not_valid_after
    crt_output['crt_serial_number'] = crt_serial_number

    return crt_output


def crt_chk_alt_name(domain, alt_name):
    for i in alt_name:
        if i[0] == "*":
            i = i[2:]
            domain = domain.replace(i, '')
            if domain.count('.') == 1:
                return True
            else:
                pass
        else:
            if i == domain:
                return True
            else:
                pass
    return False


# 检查证书是否已生效
# 检查证书是否已过期
# 检查目标域名是否在该证书中
def format_cert_key(domain_name, crt_file_name, key_file_name, crt_not_valid_before, crt_not_valid_after):
    crt_file_path = cert_file_folder + crt_file_name
    key_file_path = cert_file_folder + key_file_name

    datetime_now = datetime.utcnow()

    # 如果现在的时间大于证书生效时间，则为True
    if datetime_now >= crt_not_valid_before:
        # 如果证书失效时间-现在的时间大于配置文件中validity（单位：天）的值，则为True
        if (crt_not_valid_after - datetime_now).days >= int(config_json[domain_name]['validity']):
            crt_content = try_to_open_file(crt_file_path, 1)
            crt_base64 = base64.encodebytes(crt_content[1].encode()).decode()

            key_content = try_to_open_file(key_file_path, 1)
            key_base64 = base64.encodebytes(key_content[1].encode()).decode()

            output_dict = dict()
            output_dict['crt'] = crt_base64
            output_dict['key'] = key_base64
            return output_dict
        else:
            return False
    else:
        return False


def get_cdn_domain(config):
    # 腾讯云基础设定

    action = 'DescribeCdnHosts'
    module = 'cdn'
    params = {
        'detail': 0
    }
    # 调用API
    service = QcloudApi(module, config)
    # 可输出编码后的URL，主要用于日志，也可以生成URL后手动执行
    # 自动化应用一般不需要
    # print(service.generateUrl(action, params))
    # 执行API
    qcloud_output = service.call(action, params).decode()
    qcloud_output_json = json.loads(qcloud_output)

    cdn_host_list = []
    for i in qcloud_output_json['data']['hosts']:
        cdn_host_list.append(i['host'])

    return cdn_host_list


def write_temp_file(qcloud_output, domain, crt_serial_number):
    qcloud_output_json = json.loads(qcloud_output)
    if qcloud_output_json['code'] == 0:
        o_file = try_to_open_file(tmp_file_path, 0)
        if o_file[0]:
            content_dict = json.loads(o_file[1])

        else:
            content_dict = dict()

        o_file = open(tmp_file_path, 'w')
        content_dict[domain] = crt_serial_number
        content_dict = json.dumps(content_dict)
        o_file.write(str(content_dict))
        o_file.close()
    else:
        pass


def main_run():
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

        check_cert_info_dict = check_cert_info(cert_file_folder + cert_filename)

        open_temp_file = try_to_open_file(tmp_file_path, 0)
        if open_temp_file[0]:
            open_temp_file = json.loads(open_temp_file[1])
            if key in open_temp_file:
                if open_temp_file[key] == check_cert_info_dict['crt_serial_number']:
                    continue
                else:
                    pass
            else:
                pass
        else:
            pass

        if crt_chk_alt_name(key, check_cert_info_dict['crt_altname']):
            pass
        else:
            continue

        crt_not_valid_before = check_cert_info_dict['crt_not_valid_before']
        crt_not_valid_after = check_cert_info_dict['crt_not_valid_after']

        # 调用函数，检查证书是否合规
        crt_key_dict = format_cert_key(key, cert_filename, key_filename, crt_not_valid_before, crt_not_valid_after)

        # 不合规则跳过，进入下一循环
        if crt_key_dict:
            # 腾讯云基础设定
            config = {
                'secretId': value['secret_id'],
                'secretKey': value['secret_key'],
            }

            cdn_domain_list = get_cdn_domain(config)

            if key in cdn_domain_list:
                action = 'SetHttpsInfo'
                module = 'cdn'
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
                print(qcloud_output)
                write_temp_file(qcloud_output, key, check_cert_info_dict['crt_serial_number'])
            else:
                continue
        else:
            continue


main_run()
